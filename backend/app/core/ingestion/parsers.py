"""
Document parsers — extract raw text and page numbers from files.

Pure logic layer (Clean Architecture, ADR-001): no HTTP, no database.
Each parser yields {"text": str, "page_number": int|None} blocks.
"""

from typing import Generator


def parse_pdf(file_path: str) -> Generator[dict, None, None]:
    """PDF text extraction, page by page, using PyMuPDF (ADR: preserves reading order)."""
    import fitz  # PyMuPDF

    doc = fitz.open(file_path)
    try:
        for page_num, page in enumerate(doc, start=1):
            text = page.get_text("text")
            if text.strip():
                yield {"text": text, "page_number": page_num}
    finally:
        doc.close()


def parse_docx(file_path: str) -> Generator[dict, None, None]:
    """DOCX has no page concept at the file-format level — yield the whole document as one block."""
    from docx import Document

    doc = Document(file_path)
    full_text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    if full_text:
        yield {"text": full_text, "page_number": None}


def parse_txt(file_path: str) -> Generator[dict, None, None]:
    """Plain text / Markdown — no pagination."""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()
    if text.strip():
        yield {"text": text, "page_number": None}


_PARSERS = {"pdf": parse_pdf, "docx": parse_docx, "txt": parse_txt, "md": parse_txt}


def parse_document(file_path: str, file_type: str) -> list[dict]:
    """Dispatch to the correct parser. Raises ValueError for unsupported types."""
    parser = _PARSERS.get(file_type.lower())
    if not parser:
        raise ValueError(f"Unsupported file type: {file_type}")
    return list(parser(file_path))
