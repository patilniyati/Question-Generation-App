import io

import pytest
from docx import Document
from reportlab.pdfgen import canvas

from src.document_loader import (
    clean_text,
    extract_text,
    get_file_extension,
    is_allowed_file,
)


def test_get_file_extension():
    assert get_file_extension("Report.PDF") == "pdf"
    assert get_file_extension("my.notes.docx") == "docx"
    assert get_file_extension("README") == ""


@pytest.mark.parametrize("name", ["a.pdf", "b.DOCX", "c.txt", "d.Txt"])
def test_allowed_files(name):
    assert is_allowed_file(name)


@pytest.mark.parametrize("name", ["a.exe", "b.doc", "c.pdf.exe", "noext", "d.csv"])
def test_disallowed_files(name):
    assert not is_allowed_file(name)


def test_clean_text_normalises_line_endings_and_strips_lines():
    assert clean_text("  a  \r\n b \rc") == "a\nb\nc"


def test_clean_text_drops_blank_lines():
    # Characterisation: blank lines are removed entirely, so paragraph breaks
    # ("\n\n") never survive into the chunker for real uploads.
    assert clean_text("a\n\n\nb") == "a\nb"


def test_extract_text_txt(make_upload):
    upload = make_upload("notes.txt", "Hello\n\nWorld ✓".encode("utf-8"))
    assert extract_text(upload) == "Hello\nWorld ✓"


def test_extract_text_txt_ignores_undecodable_bytes(make_upload):
    upload = make_upload("notes.txt", b"good \xff\xfe text")
    assert extract_text(upload) == "good  text"


def test_extract_text_docx_skips_empty_paragraphs(make_upload):
    document = Document()
    document.add_paragraph("First paragraph.")
    document.add_paragraph("   ")
    document.add_paragraph("Second paragraph.")
    buffer = io.BytesIO()
    document.save(buffer)

    upload = make_upload("lesson.docx", buffer.getvalue())

    assert extract_text(upload) == "First paragraph.\nSecond paragraph."


def test_extract_text_pdf_reads_every_page(make_upload):
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.drawString(72, 750, "Photosynthesis happens in chloroplasts.")
    pdf.showPage()
    pdf.drawString(72, 750, "Mitochondria produce ATP.")
    pdf.showPage()
    pdf.save()

    text = extract_text(make_upload("bio.pdf", buffer.getvalue()))

    assert "Photosynthesis happens in chloroplasts." in text
    assert "Mitochondria produce ATP." in text


def test_extract_text_unsupported_type_raises(make_upload):
    with pytest.raises(ValueError, match="Unsupported file type"):
        extract_text(make_upload("data.csv", b"a,b"))
