"""Extracts plain text from supported document formats."""

from pathlib import Path

from docx import Document
from pypdf import PdfReader

from src.core.exceptions import ValidationError


class DocumentParser:
    """Parses PDF, DOCX, and TXT files into raw text."""

    def parse(self, path: Path) -> str:
        suffix = path.suffix.lower()
        if suffix == ".txt":
            return path.read_text(encoding="utf-8", errors="ignore")
        if suffix == ".docx":
            document = Document(str(path))
            return "\n".join(paragraph.text for paragraph in document.paragraphs if paragraph.text.strip())
        if suffix == ".pdf":
            reader = PdfReader(str(path))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        raise ValidationError("Unsupported file type. Use PDF, DOCX, or TXT.")
