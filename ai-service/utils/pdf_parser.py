import re
from io import BytesIO
from typing import Optional

import pdfplumber
from PyPDF2 import PdfReader


def sanitize_text(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    cleaned = re.sub(r"[^\x20-\x7E\n\r\t]", "", cleaned)
    return cleaned


def extract_text_from_pdf_bytes(data: bytes) -> str:
    text_chunks: list[str] = []

    try:
        with pdfplumber.open(BytesIO(data)) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text() or ""
                if extracted:
                    text_chunks.append(extracted)
    except Exception:
        # Fall back to PyPDF2 parser for malformed PDFs.
        reader = PdfReader(BytesIO(data))
        for page in reader.pages:
            extracted = page.extract_text() or ""
            if extracted:
                text_chunks.append(extracted)

    return sanitize_text("\n".join(text_chunks))


def validate_upload_size(data: bytes, max_mb: int) -> Optional[str]:
    size_mb = len(data) / (1024 * 1024)
    if size_mb > max_mb:
        return f"File is too large ({size_mb:.2f}MB). Max allowed is {max_mb}MB."
    return None