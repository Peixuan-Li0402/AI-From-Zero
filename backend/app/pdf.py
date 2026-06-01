import tempfile
from pathlib import Path

import PyPDF2
import pdfplumber


def _extract_with_pdfplumber(path: Path) -> list[dict]:
    pages = []
    with pdfplumber.open(str(path)) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            page_text = page.extract_text() or ""
            pages.append({"page": page_num, "text": page_text, "length": len(page_text)})
    return pages


def _extract_with_pypdf2(path: Path) -> list[dict]:
    pages = []
    with path.open("rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page_num, page in enumerate(reader.pages, 1):
            page_text = page.extract_text() or ""
            pages.append({"page": page_num, "text": page_text, "length": len(page_text)})
    return pages


def extract_pdf_pages(content: bytes) -> dict:
    if not content:
        raise ValueError("PDF文件为空")

    tmp_path = None
    warnings = []
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)

        try:
            pages = _extract_with_pdfplumber(tmp_path)
            engine = "pdfplumber"
        except Exception as e:
            warnings.append(f"pdfplumber 解析失败，已切换到 PyPDF2：{e}")
            pages = _extract_with_pypdf2(tmp_path)
            engine = "PyPDF2"

        text = "\n\n".join(
            f"--- 第{page['page']}页 ---\n\n{page['text']}".strip()
            for page in pages
            if page.get("text", "").strip()
        )
        return {
            "text": text,
            "pages": pages,
            "pageCount": len(pages),
            "textLength": len(text),
            "engine": engine,
            "warnings": warnings,
        }
    finally:
        if tmp_path:
            try:
                tmp_path.unlink()
            except OSError:
                pass


def extract_pdf_text(content: bytes) -> str:
    return extract_pdf_pages(content)["text"]
