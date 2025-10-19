from __future__ import annotations

from io import BytesIO
from typing import Optional

from bs4 import BeautifulSoup
from fastapi import HTTPException, status
from pypdf import PdfReader


TEXT_TYPES = {"text/plain", "text/markdown"}
HTML_TYPES = {"text/html"}
PDF_TYPES = {"application/pdf"}


def _parse_text_bytes(data: bytes) -> str:
    return data.decode("utf-8", errors="ignore")


def _parse_html_bytes(data: bytes) -> str:
    soup = BeautifulSoup(data, "html.parser")
    return soup.get_text(" ", strip=True)


def _parse_pdf_bytes(data: bytes) -> str:
    # Extract text from PDF; if none, likely scanned
    reader = PdfReader(BytesIO(data))
    texts: list[str] = []
    for page in reader.pages:
        try:
            page_text = page.extract_text() or ""
        except Exception:
            page_text = ""
        if page_text:
            texts.append(page_text)
    text = "\n".join(t.strip() for t in texts if t.strip())
    if not text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scanned PDFs are not supported in MVP (no extractable text).",
        )
    return text


def parse_from_bytes(filename: str, content_type: Optional[str], data: bytes) -> str:
    """Parse text from bytes based on content type or filename.

    Supported: text, markdown, html, pdf. Raises HTTPException for unsupported types
    or empty content.
    """
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file uploaded.",
        )

    ctype = (content_type or "").lower()
    name = filename.lower()

    text: str
    if ctype in TEXT_TYPES or name.endswith(".txt") or name.endswith(".md") or name.endswith(".markdown"):
        text = _parse_text_bytes(data)
    elif ctype in HTML_TYPES or name.endswith(".html") or name.endswith(".htm"):
        text = _parse_html_bytes(data)
    elif ctype in PDF_TYPES or name.endswith(".pdf"):
        text = _parse_pdf_bytes(data)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Please upload txt, md, html, or pdf.",
        )

    if not text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No extractable text found in the document.",
        )
    return text
