import io
from pathlib import Path

from pypdf import PdfReader
from docx import Document as DocxDocument

from src.config import ALLOWED_EXTENSIONS


def get_file_extension(filename: str) -> str:
    return Path(filename).suffix.lower().replace(".", "")


def is_allowed_file(filename: str) -> bool:
    return get_file_extension(filename) in ALLOWED_EXTENSIONS


def extract_text_from_pdf(file) -> str:
    reader = PdfReader(io.BytesIO(file.getvalue()))
    pages = []

    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append(text.strip())

    return "\n\n".join(pages)


def extract_text_from_docx(file) -> str:
    document = DocxDocument(io.BytesIO(file.getvalue()))
    paragraphs = [paragraph.text.strip() for paragraph in document.paragraphs]
    return "\n".join(paragraph for paragraph in paragraphs if paragraph)


def extract_text_from_txt(file) -> str:
    return file.getvalue().decode("utf-8", errors="ignore")


def extract_text(file) -> str:
    extension = get_file_extension(file.name)

    if extension == "pdf":
        text = extract_text_from_pdf(file)
    elif extension == "docx":
        text = extract_text_from_docx(file)
    elif extension == "txt":
        text = extract_text_from_txt(file)
    else:
        raise ValueError("Unsupported file type.")

    return clean_text(text)


def clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = "\n".join(line.strip() for line in text.split("\n"))
    text = "\n".join(line for line in text.split("\n") if line)

    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")

    return text.strip()