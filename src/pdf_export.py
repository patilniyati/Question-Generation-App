import io
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

PLUM = colors.HexColor("#935073")
GREEN = colors.HexColor("#50D255")
PEACH = colors.HexColor("#F6DBC0")
CREAM = colors.HexColor("#F8F4E9")
INK = colors.HexColor("#2E2230")

ANSWERS_PER_ROW = 5


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()["Normal"]

    return {
        "title": ParagraphStyle(
            "QuizTitle", parent=base, fontName="Helvetica-Bold", fontSize=20,
            leading=24, textColor=PLUM, spaceAfter=4,
        ),
        "subtitle": ParagraphStyle(
            "QuizSubtitle", parent=base, fontSize=10, leading=14,
            textColor=colors.HexColor("#6E5A68"), spaceAfter=10,
        ),
        "question": ParagraphStyle(
            "Question", parent=base, fontName="Helvetica-Bold", fontSize=11,
            leading=15, textColor=INK, spaceAfter=5,
        ),
        "option": ParagraphStyle(
            "Option", parent=base, fontSize=10.5, leading=14, textColor=INK,
            leftIndent=18, spaceAfter=2,
        ),
        "key_title": ParagraphStyle(
            "KeyTitle", parent=base, fontName="Helvetica-Bold", fontSize=20,
            leading=24, textColor=PLUM, spaceAfter=4,
        ),
        "key_cell": ParagraphStyle(
            "KeyCell", parent=base, fontName="Helvetica-Bold", fontSize=12,
            leading=16, alignment=TA_CENTER, textColor=INK,
        ),
    }


def _draw_page_chrome(canvas, doc):
    canvas.saveState()
    width, height = A4

    canvas.setFillColor(PLUM)
    canvas.rect(0, height - 6 * mm, width, 6 * mm, stroke=0, fill=1)
    canvas.setFillColor(GREEN)
    canvas.rect(0, height - 6 * mm, 28 * mm, 6 * mm, stroke=0, fill=1)

    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(colors.HexColor("#6E5A68"))
    canvas.drawCentredString(width / 2, 10 * mm, f"Page {doc.page}")
    canvas.restoreState()


def _answer_key_table(questions: list[dict], styles: dict) -> Table:
    cells = [
        Paragraph(f"{number}. {escape(str(q['correct_answer']).strip().upper())}", styles["key_cell"])
        for number, q in enumerate(questions, start=1)
    ]

    while len(cells) % ANSWERS_PER_ROW:
        cells.append("")

    rows = [
        cells[i : i + ANSWERS_PER_ROW] for i in range(0, len(cells), ANSWERS_PER_ROW)
    ]

    table = Table(rows, colWidths=[(A4[0] - 40 * mm) / ANSWERS_PER_ROW] * ANSWERS_PER_ROW)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), CREAM),
                ("BOX", (0, 0), (-1, -1), 0.8, PLUM),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, PEACH),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return table


def build_quiz_pdf(questions: list[dict], title: str, subtitle: str = "") -> bytes:
    """Questions first, then a single answer-key page at the end."""
    styles = _styles()
    buffer = io.BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        title=title,
    )

    story = [Paragraph(escape(title), styles["title"])]

    if subtitle:
        story.append(Paragraph(escape(subtitle), styles["subtitle"]))

    story.append(Spacer(1, 4 * mm))

    for number, question in enumerate(questions, start=1):
        block = [Paragraph(f"{number}. {escape(question['question'])}", styles["question"])]

        for letter in ["A", "B", "C", "D"]:
            block.append(
                Paragraph(f"<b>{letter}.</b>&nbsp; {escape(question['options'][letter])}", styles["option"])
            )

        block.append(Spacer(1, 6 * mm))
        story.append(KeepTogether(block))

    story.append(PageBreak())
    story.append(Paragraph("Answer Key", styles["key_title"]))
    story.append(Paragraph(escape(title), styles["subtitle"]))
    story.append(Spacer(1, 4 * mm))
    story.append(_answer_key_table(questions, styles))

    document.build(story, onFirstPage=_draw_page_chrome, onLaterPages=_draw_page_chrome)
    return buffer.getvalue()
