import io

from helpers import make_question
from pypdf import PdfReader

from src.pdf_export import build_quiz_pdf


def read_pages(pdf_bytes: bytes) -> list[str]:
    return [page.extract_text() for page in PdfReader(io.BytesIO(pdf_bytes)).pages]


def build(questions, title="Photosynthesis", subtitle="bio.pdf · Medium"):
    return read_pages(build_quiz_pdf(questions, title=title, subtitle=subtitle))


def test_output_is_a_valid_pdf(questions):
    pdf = build_quiz_pdf(questions, "Title")

    assert pdf.startswith(b"%PDF")
    assert len(PdfReader(io.BytesIO(pdf)).pages) >= 2


def test_answer_key_is_a_single_final_page(questions):
    pages = build(questions)

    assert "Answer Key" in pages[-1]
    assert not any("Answer Key" in page for page in pages[:-1])


def test_answers_appear_only_on_the_last_page():
    qs = [make_question(i, correct_answer="C") for i in range(3)]
    pages = build(qs)

    assert "1. C" in pages[-1]
    assert "2. C" in pages[-1]
    assert "3. C" in pages[-1]
    # question pages list options "A." .. "D." but never an "N. C" answer line
    for page in pages[:-1]:
        assert "1. C" not in page
        assert "Correct" not in page
        assert "Because the text says so." not in page  # explanation never leaks


def test_question_pages_contain_questions_and_all_options(questions):
    first_pages = "\n".join(build(questions)[:-1])

    for number in range(1, 6):
        assert f"{number}. What is the answer to question number {number}?" in first_pages
    for option in ("Alpha", "Bravo", "Charlie", "Delta"):
        assert option in first_pages


def test_title_and_subtitle_are_printed(questions):
    first_page = build(questions)[0]

    assert "Photosynthesis" in first_page
    assert "bio.pdf" in first_page


def test_many_questions_flow_over_multiple_pages_but_one_answer_page():
    qs = [make_question(i) for i in range(15)]
    pages = build(qs)

    assert len(pages) >= 3
    assert sum("Answer Key" in page for page in pages) == 1
    assert "15." in pages[-1]  # all 15 answers fit on the single final page


def test_special_characters_are_escaped_not_interpreted():
    nasty = make_question(
        0, question="Is 5 < 6 & 7 > 3? <b>bold</b>",
        options={"A": "<i>x</i>", "B": "a & b", "C": "c", "D": "d"},
    )
    pages = build([nasty])

    assert "5 < 6 & 7 > 3? <b>bold</b>" in pages[0]
    assert "<i>x</i>" in pages[0]


def test_lowercase_answers_are_uppercased_in_the_key():
    pages = build([make_question(0, correct_answer=" b ")])

    assert "1. B" in pages[-1]


def test_single_question_still_gets_an_answer_page():
    pages = build([make_question(0)])

    assert len(pages) == 2
    assert "Answer Key" in pages[1]
