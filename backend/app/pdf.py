import tempfile
from pathlib import Path
import re

from pypdf import PdfReader
import pdfplumber


SECTION_PATTERNS = [
    ("abstract", r"^(abstract|摘要)\b"),
    ("introduction", r"^(\d+\s*)?(introduction|intro|引言|绪论)\b"),
    ("related_work", r"^(\d+\s*)?(related work|background|preliminaries|相关工作|背景|预备知识)\b"),
    ("method", r"^(\d+\s*)?(method|methods|methodology|approach|model|方法|模型|算法)\b"),
    ("experiments", r"^(\d+\s*)?(experiments|evaluation|results|实验|评估|结果)\b"),
    ("discussion", r"^(\d+\s*)?(discussion|analysis|讨论|分析)\b"),
    ("conclusion", r"^(\d+\s*)?(conclusion|conclusions|结论|总结)\b"),
    ("references", r"^(references|bibliography|参考文献)\b"),
]


def _long_alpha_tokens(text: str) -> int:
    return sum(1 for token in re.findall(r"[A-Za-z]{24,}", text or ""))


def _text_quality_score(text: str) -> float:
    if not text:
        return -10_000
    alpha = len(re.findall(r"[A-Za-z]", text))
    spaces = text.count(" ")
    newlines = text.count("\n")
    long_tokens = _long_alpha_tokens(text)
    space_ratio = spaces / max(alpha, 1)
    score = len(text) * 0.02 + spaces * 1.4 + newlines * 0.6
    score -= long_tokens * 90
    if alpha > 200 and space_ratio < 0.08:
        score -= 500
    return score


def _extract_pdfplumber_page_text(page) -> tuple[str, str]:
    candidates: list[tuple[str, str]] = []
    extract_configs = [
        ("tight-spacing", {"x_tolerance": 1, "y_tolerance": 3, "keep_blank_chars": False}),
        ("default", {}),
    ]
    for name, kwargs in extract_configs:
        try:
            candidates.append((name, page.extract_text(**kwargs) or ""))
        except Exception:
            continue
    try:
        words = page.extract_words(x_tolerance=1, y_tolerance=3, keep_blank_chars=False)
        candidates.append(("word-stream", " ".join(word.get("text", "") for word in words)))
    except Exception:
        pass
    if not candidates:
        return "", "empty"
    return max(candidates, key=lambda item: _text_quality_score(item[1]))


def _extract_with_pdfplumber(path: Path) -> list[dict]:
    pages = []
    with pdfplumber.open(str(path)) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            profile, page_text = _extract_pdfplumber_page_text(page)
            pages.append({"page": page_num, "text": page_text, "length": len(page_text), "profile": profile})
    return pages


def _extract_with_pypdf(path: Path) -> list[dict]:
    pages = []
    with path.open("rb") as f:
        reader = PdfReader(f)
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
            warnings.append(f"pdfplumber 解析失败，已切换到 pypdf：{e}")
            pages = _extract_with_pypdf(tmp_path)
            engine = "pypdf"

        text = "\n\n".join(
            f"--- 第{page['page']}页 ---\n\n{page['text']}".strip()
            for page in pages
            if page.get("text", "").strip()
        )
        if _long_alpha_tokens(text) > max(8, len(pages) * 2):
            warnings.append("PDF 文本可能粘连；可上传可复制文本版 PDF。")
        return {
            "text": text,
            "pages": pages,
            "pageCount": len(pages),
            "textLength": len(text),
            "engine": engine,
            "structure": analyze_text_structure(text, pages),
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


def _normalize_line(line: str) -> str:
    return re.sub(r"\s+", " ", line.strip())


def _looks_like_heading(line: str) -> tuple[str, str] | None:
    clean = _normalize_line(line)
    if not clean or len(clean) > 120:
        return None
    lower = clean.lower().strip(" .:：")
    for section_type, pattern in SECTION_PATTERNS:
        if re.search(pattern, lower, re.IGNORECASE):
            return section_type, clean
    if re.fullmatch(r"\d+(\.\d+)*\.?\s+[A-Z][A-Za-z0-9 ,:/()-]{2,80}", clean):
        return "section", clean
    return None


def _extract_title(lines: list[str]) -> str:
    candidates = []
    for line in lines[:30]:
        clean = _normalize_line(line)
        if not clean or clean.startswith("---") or len(clean) < 8:
            continue
        if _looks_like_heading(clean):
            continue
        if len(clean) <= 160:
            candidates.append(clean)
    return candidates[0] if candidates else ""


def _extract_references(text: str) -> list[dict]:
    ref_match = re.search(r"(references|bibliography|参考文献)\s*(.+)$", text, re.IGNORECASE | re.DOTALL)
    if not ref_match:
        return []
    ref_text = ref_match.group(2)
    raw_items = re.split(r"\n\s*(?:\[\d+\]|\d+\.\s+)", ref_text)
    references = []
    for idx, item in enumerate(raw_items[:60], 1):
        clean = _normalize_line(item)
        if len(clean) < 20:
            continue
        year_match = re.search(r"(19|20)\d{2}", clean)
        references.append({
            "index": idx,
            "text": clean[:500],
            "year": year_match.group(0) if year_match else "",
        })
    return references[:40]


def _extract_citations(text: str) -> list[dict]:
    citation_counter: dict[str, int] = {}
    for match in re.findall(r"\[(\d+(?:\s*,\s*\d+)*)\]", text):
        for number in re.split(r"\s*,\s*", match):
            citation_counter[f"[{number}]"] = citation_counter.get(f"[{number}]", 0) + 1
    for match in re.findall(r"\(([A-Z][A-Za-z-]+(?:\s+et\s+al\.)?,?\s+(?:19|20)\d{2})\)", text):
        citation_counter[match] = citation_counter.get(match, 0) + 1
    return [
        {"marker": marker, "count": count}
        for marker, count in sorted(citation_counter.items(), key=lambda item: (-item[1], item[0]))[:30]
    ]


def analyze_text_structure(text: str, pages: list[dict] | None = None) -> dict:
    lines = [line for line in text.splitlines() if line.strip()]
    sections = []
    current = None
    for line in lines:
        heading = _looks_like_heading(line)
        if heading:
            if current:
                current["textPreview"] = _normalize_line(" ".join(current.pop("_buffer", [])))[:700]
                sections.append(current)
            section_type, title = heading
            current = {"type": section_type, "title": title, "_buffer": []}
            continue
        if current:
            current["_buffer"].append(line.strip())
    if current:
        current["textPreview"] = _normalize_line(" ".join(current.pop("_buffer", [])))[:700]
        sections.append(current)

    abstract = ""
    for section in sections:
        if section["type"] == "abstract":
            abstract = section.get("textPreview", "")
            break

    references = _extract_references(text)
    citations = _extract_citations(text)
    reading_anchors = [
        {"id": "abstract", "label": "先读摘要", "sectionType": "abstract"},
        {"id": "method", "label": "再看方法", "sectionType": "method"},
        {"id": "experiments", "label": "检查实验", "sectionType": "experiments"},
        {"id": "references", "label": "追溯引用", "sectionType": "references"},
    ]
    available_types = {section["type"] for section in sections}
    for anchor in reading_anchors:
        anchor["available"] = anchor["sectionType"] in available_types

    return {
        "titleGuess": _extract_title(lines),
        "abstractGuess": abstract,
        "sections": sections[:24],
        "references": references,
        "citations": citations,
        "readingAnchors": reading_anchors,
        "pageCount": len(pages or []),
        "parser": "local-heuristic",
    }
