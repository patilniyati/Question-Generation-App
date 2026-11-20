from html import escape

import streamlit as st

from src.auth import AuthError, authenticate_user, register_user
from src.config import BASE_DIR, GROQ_API_KEY, MAX_UPLOAD_MB
from src.database import delete_quiz, init_db, list_quizzes, save_quiz
from src.document_loader import extract_text, is_allowed_file
from src.mcq_generator import generate_mcqs, get_groq_client
from src.pdf_export import build_quiz_pdf
from src.text_chunker import chunk_text
from src.validator import validate_questions

st.set_page_config(
    page_title="AI MCQ Generator",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

with open(BASE_DIR / "assets" / "style.css", encoding="utf-8") as css_file:
    st.html(f"<style>{css_file.read()}</style>")

init_db()

PAGE_GENERATE = "✨ Generate quiz"
PAGE_HISTORY = "🕘 My history"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main():
    user = st.session_state.get("user")

    if not user:
        render_auth_page()
        return

    page = render_sidebar(user)

    if page == PAGE_HISTORY:
        render_history_page(user)
    else:
        render_generator_page(user)


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------


def render_auth_page():
    _, centre, _ = st.columns([1, 1.4, 1])

    with centre:
        st.markdown(
            """
            <div class="auth-brand">
                <h1>🧠 AI MCQ Generator</h1>
                <p>Turn any document into a ready-to-print quiz. Sign in to keep your quiz history.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        sign_in_tab, sign_up_tab = st.tabs(["Sign in", "Create account"])

        with sign_in_tab:
            with st.form("sign_in_form"):
                email = st.text_input("Email", placeholder="teacher@school.edu")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button(
                    "Sign in", type="primary", width="stretch"
                )

            if submitted:
                try:
                    st.session_state["user"] = authenticate_user(email, password)
                except AuthError as error:
                    st.error(str(error))
                else:
                    st.rerun()

        with sign_up_tab:
            with st.form("sign_up_form"):
                name = st.text_input("Full name", placeholder="Jane Smith")
                email = st.text_input(
                    "Email", placeholder="teacher@school.edu", key="signup_email"
                )
                password = st.text_input(
                    "Password", type="password", key="signup_password",
                    help="At least 8 characters.",
                )
                confirm_password = st.text_input("Confirm password", type="password")
                submitted = st.form_submit_button(
                    "Create account", type="primary", width="stretch"
                )

            if submitted:
                try:
                    st.session_state["user"] = register_user(
                        name, email, password, confirm_password
                    )
                except AuthError as error:
                    st.error(str(error))
                else:
                    st.rerun()


def render_sidebar(user: dict) -> str:
    with st.sidebar:
        st.markdown(
            f"""
            <div class="user-chip">
                <div class="name">👋 {escape(user['name'])}</div>
                <div class="email">{escape(user['email'])}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        page = st.radio(
            "Navigate",
            [PAGE_GENERATE, PAGE_HISTORY],
            label_visibility="collapsed",
        )

        st.divider()

        if st.button("Sign out", width="stretch"):
            st.session_state.clear()
            st.rerun()

    return page


# ---------------------------------------------------------------------------
# Generator page
# ---------------------------------------------------------------------------


def render_header(title: str, subtitle: str):
    st.markdown(
        f"""
        <div class="main-header">
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_step_title(number: int, text: str):
    st.markdown(
        f'<div class="step-title"><span class="step-num">{number}</span>{text}</div>',
        unsafe_allow_html=True,
    )


def render_empty_state():
    st.markdown(
        """
        <div class="empty-state">
            <h3>How it works</h3>
            <div class="how-step"><span class="step-num">1</span> Upload a PDF, DOCX or TXT document</div>
            <div class="how-step"><span class="step-num">2</span> Choose how many questions and how hard</div>
            <div class="how-step"><span class="step-num">3</span> Review the questions, then download the PDF</div>
            <p style="margin-top: 0.9rem;">Every quiz is saved to your history automatically.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_file_summary(file_name: str, word_count: int, chunk_count: int):
    st.markdown(
        f"""
        <div class="file-summary">
            <span class="file-name">📄 {escape(file_name)}</span>
            <span class="pill green">{word_count:,} words</span>
            <span class="pill">{chunk_count} text chunk(s)</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_generator_page(user: dict):
    render_header(
        "🧠 AI MCQ Generator for Teachers",
        "Upload a document, choose quiz settings, and generate review-ready multiple-choice questions.",
    )

    left, right = st.columns([1, 1.8], gap="large")

    with left:
        with st.container(border=True, key="upload_card"):
            render_step_title(1, "Upload document")

            uploaded_file = st.file_uploader(
                "Upload a document",
                type=["pdf", "docx", "txt"],
                label_visibility="collapsed",
                help=f"Supported formats: PDF, DOCX, TXT. Maximum size: {MAX_UPLOAD_MB} MB.",
            )

            if uploaded_file:
                if uploaded_file.size > MAX_UPLOAD_MB * 1024 * 1024:
                    st.error(f"File is larger than {MAX_UPLOAD_MB} MB.")
                    return

                if not is_allowed_file(uploaded_file.name):
                    st.error("Unsupported file type.")
                    return

        with st.container(border=True, key="settings_card"):
            render_step_title(2, "Quiz settings")

            num_questions = st.slider("Number of questions", 3, 15, 5)
            difficulty = st.selectbox(
                "Difficulty",
                ["easy", "medium", "hard", "mixed"],
                index=1,
            )
            topic = st.text_input(
                "Topic focus (optional)",
                placeholder="e.g. Photosynthesis, World War II",
            )

            generate_clicked = st.button(
                "✨ Generate MCQs",
                width="stretch",
                type="primary",
            )

    with right:
        if not uploaded_file:
            render_empty_state()
            return

        with st.spinner("Extracting text from document..."):
            try:
                document_text = extract_text(uploaded_file)
            except Exception as error:
                st.error(f"Could not read the document: {error}")
                return

        if len(document_text.strip()) < 200:
            st.error(
                "The document does not contain enough readable text. "
                "Scanned PDFs may require OCR."
            )
            return

        chunks = chunk_text(document_text)

        render_file_summary(uploaded_file.name, len(document_text.split()), len(chunks))

        with st.expander("Preview extracted text"):
            st.text_area(
                "Extracted text",
                document_text[:5000],
                height=250,
                disabled=True,
            )

        if generate_clicked:
            if not GROQ_API_KEY:
                st.error("Missing GROQ_API_KEY. Add it to your .env file.")
                return

            selected_chunk = chunks[0]

            with st.spinner("Generating MCQs with Groq..."):
                try:
                    client = get_groq_client(GROQ_API_KEY)

                    questions = generate_mcqs(
                        client=client,
                        chunk=selected_chunk,
                        num_questions=num_questions,
                        difficulty=difficulty,
                        topic=topic,
                    )

                    valid_questions, invalid_questions = validate_questions(questions)

                except Exception as error:
                    st.error(f"MCQ generation failed: {error}")
                    return

            quiz_id = None

            if valid_questions:
                quiz_id = save_quiz(
                    user_id=user["id"],
                    document_name=uploaded_file.name,
                    difficulty=difficulty,
                    topic=topic,
                    questions=valid_questions,
                )

            st.session_state["current_quiz"] = {
                "id": quiz_id,
                "title": topic.strip() or uploaded_file.name,
                "document_name": uploaded_file.name,
                "difficulty": difficulty,
                "questions": valid_questions,
                "invalid": invalid_questions,
            }

        quiz = st.session_state.get("current_quiz")

        if quiz:
            display_generated_quiz(quiz)


def display_generated_quiz(quiz: dict):
    st.subheader("📝 Generated MCQs")

    questions = quiz["questions"]

    if not questions:
        st.warning("No valid questions were generated. Try again or use a clearer document.")
        render_invalid_questions(quiz["invalid"])
        return

    st.success(
        f"{len(questions)} valid MCQ(s) generated from **{quiz['document_name']}** "
        "and saved to your history."
    )

    render_pdf_download(
        questions=questions,
        title=quiz["title"],
        document_name=quiz["document_name"],
        difficulty=quiz["difficulty"],
        key=f"pdf_current_{quiz['id']}",
    )

    render_question_cards(questions)
    render_invalid_questions(quiz["invalid"])


# ---------------------------------------------------------------------------
# History page
# ---------------------------------------------------------------------------


def render_history_page(user: dict):
    render_header(
        "🕘 My quiz history",
        "Every quiz you generate is saved here. Re-read it or download the PDF again.",
    )

    quizzes = list_quizzes(user["id"])

    if not quizzes:
        st.markdown(
            """
            <div class="empty-state" style="text-align: center;">
                <h3>No quizzes yet</h3>
                <p>Generate your first quiz and it will show up here.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    st.caption(f"{len(quizzes)} saved quiz(zes)")

    for quiz in quizzes:
        created = quiz["created_at"].strftime("%d %b %Y, %H:%M")
        label = f"{quiz['title']}  ·  {created}"

        with st.expander(label):
            st.markdown(
                f"""
                <div class="history-meta">
                    <span class="pill">{escape(quiz['difficulty'])}</span>
                    <span class="pill green">{len(quiz['questions'])} questions</span>
                    <span class="pill">📄 {escape(quiz['document_name'])}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            download_col, delete_col = st.columns(2)

            with download_col:
                render_pdf_download(
                    questions=quiz["questions"],
                    title=quiz["title"],
                    document_name=quiz["document_name"],
                    difficulty=quiz["difficulty"],
                    key=f"pdf_history_{quiz['id']}",
                )

            with delete_col:
                if st.button(
                    "🗑️ Delete quiz",
                    key=f"delete_{quiz['id']}",
                    width="stretch",
                ):
                    delete_quiz(user["id"], quiz["id"])

                    current = st.session_state.get("current_quiz")
                    if current and current.get("id") == quiz["id"]:
                        st.session_state.pop("current_quiz")

                    st.rerun()

            render_question_cards(quiz["questions"])


# ---------------------------------------------------------------------------
# Shared rendering
# ---------------------------------------------------------------------------


def render_question_cards(questions: list[dict]):
    for index, question in enumerate(questions, start=1):
        options = question["options"]

        st.markdown(
            f"""
            <div class="mcq-card">
                <div class="mcq-question">Q{index}. {escape(question['question'])}</div>
                <div class="mcq-option"><strong>A.</strong> {escape(options['A'])}</div>
                <div class="mcq-option"><strong>B.</strong> {escape(options['B'])}</div>
                <div class="mcq-option"><strong>C.</strong> {escape(options['C'])}</div>
                <div class="mcq-option"><strong>D.</strong> {escape(options['D'])}</div>
                <div class="correct-answer">
                    ✅ Correct answer: {escape(str(question['correct_answer']).strip().upper())}
                </div>
                <div class="source-text">
                    <strong>Explanation:</strong> {escape(question['explanation'])}<br><br>
                    <strong>Source:</strong> {escape(question.get('source_text') or 'Not provided')}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_invalid_questions(invalid_questions: list[dict]):
    if not invalid_questions:
        return

    with st.expander(f"⚠️ {len(invalid_questions)} question(s) failed validation"):
        for item in invalid_questions:
            errors = "<br>".join(escape(error) for error in item["errors"])

            st.markdown(
                f"""
                <div class="error-box">
                    <strong>Question {item['index']} was rejected.</strong><br>
                    {errors}
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_pdf_download(
    questions: list[dict],
    title: str,
    document_name: str,
    difficulty: str,
    key: str,
):
    subtitle = f"{document_name}  ·  {difficulty.title()}  ·  {len(questions)} questions"
    pdf_bytes = build_quiz_pdf(questions, title=title, subtitle=subtitle)

    st.download_button(
        label="⬇️ Download PDF (questions + answer key)",
        data=pdf_bytes,
        file_name="mcq_quiz.pdf",
        mime="application/pdf",
        type="primary",
        width="stretch",
        key=key,
    )


if __name__ == "__main__":
    main()