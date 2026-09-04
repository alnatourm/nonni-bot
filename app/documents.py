import io
from pathlib import Path

from docx import Document
from pypdf import PdfReader


SUPPORTED_DOCUMENTS = {".txt", ".md", ".csv", ".json", ".pdf", ".docx"}


def extract_document(data: bytes, filename: str, max_chars: int) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_DOCUMENTS:
        raise ValueError("Unsupported document type")

    if suffix == ".pdf":
        reader = PdfReader(io.BytesIO(data))
        text = "\n\n".join(page.extract_text() or "" for page in reader.pages)
    elif suffix == ".docx":
        document = Document(io.BytesIO(data))
        text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    else:
        text = data.decode("utf-8", errors="replace")

    text = text.strip()
    if not text:
        raise ValueError("No readable text found in document")
    return text[:max_chars]
