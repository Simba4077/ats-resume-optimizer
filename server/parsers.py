from io import BytesIO
from typing import Tuple
from pdfminer.high_level import extract_text as pdf_extract_text
from docx import Document

import tempfile
from pdfminer.high_level import extract_text as pdf_extract_text

def _from_pdf(data: bytes) -> str:
    try:
        # Write PDF bytes to a temporary file because pdfminer expects a file path
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(data)
            tmp.flush()
            text = pdf_extract_text(tmp.name) or ""
        return text
    except Exception as e:
        print(f"[PDF ERROR] {e}")
        return ""


def _from_docx(data: bytes) -> str:
    try:
        bio = BytesIO(data)
        doc = Document(bio)
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception as e:
        print(f"[DOCX ERROR] {e}")
        return ""

def _from_txt(data: bytes) -> str:
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("latin-1", errors="ignore")

def read_text(filename: str, data: bytes) -> Tuple[str, str]:
    """
    Read text directly from PDF, DOCX, or TXT without temp files.
    Works cross-platform.
    """
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return ("pdf", _from_pdf(data))
    if lower.endswith(".docx"):
        return ("docx", _from_docx(data))
    if lower.endswith(".txt") or lower.endswith(".md"):
        return ("txt", _from_txt(data))
    return ("unknown", _from_txt(data))
