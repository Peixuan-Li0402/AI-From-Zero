from __future__ import annotations

import re
from collections import Counter

import httpx

from .terms import related_papers_for_term, terms


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _paper_key(paper: dict) -> str:
    return _clean(paper.get("title", "")).lower()


def _local_paper_search(query: str, limit: int) -> list[dict]:
    q = query.lower().strip()
    scored = []
    for term in terms:
        haystack = " ".join([
            term.get("term", ""),
            term.get("termEn", ""),
            term.get("termZh", ""),
            term.get("category", ""),
            " ".join(term.get("aliases", [])),
            " ".join(term.get("aliasesEn", [])),
            " ".join(term.get("aliasesZh", [])),
        ]).lower()
        if q and q not in haystack:
            continue
        score = 4 if q and term.get("term", "").lower() == q else 1
        for paper in related_papers_for_term(term):
            item = dict(paper)
            item["source"] = "local-kb"
            item["fromTerm"] = term.get("term", "")
            scored.append((score, item))
    seen = set()
    results = []
    for _, paper in sorted(scored, key=lambda item: item[0], reverse=True):
        key = _paper_key(paper)
        if not key or key in seen:
            continue
        seen.add(key)
        results.append(paper)
        if len(results) >= limit:
            break
    return results


def _openalex_search(query: str, limit: int) -> list[dict]:
    params = {
        "search": query,
        "per-page": min(limit, 10),
        "select": "title,publication_year,authorships,cited_by_count,doi,open_access,primary_location",
    }
    with httpx.Client(timeout=6.0, follow_redirects=True) as client:
        resp = client.get("https://api.openalex.org/works", params=params)
        resp.raise_for_status()
        data = resp.json()
    results = []
    for work in data.get("results", []):
        authors = ", ".join(
            item.get("author", {}).get("display_name", "")
            for item in work.get("authorships", [])[:4]
            if item.get("author", {}).get("display_name")
        )
        location = work.get("primary_location") or {}
        pdf_url = (work.get("open_access") or {}).get("oa_url") or (location.get("landing_page_url") if isinstance(location, dict) else "")
        results.append({
            "title": _clean(work.get("title", "")),
            "authors": authors,
            "year": work.get("publication_year") or "",
            "citationCount": work.get("cited_by_count") or 0,
            "url": work.get("doi") or pdf_url or "",
            "openAccessUrl": pdf_url or "",
            "source": "openalex",
            "shortDesc": "OpenAlex scholarly metadata result.",
        })
    return [item for item in results if item.get("title")]


def _semantic_scholar_search(query: str, limit: int) -> list[dict]:
    params = {
        "query": query,
        "limit": min(limit, 10),
        "fields": "title,authors,year,citationCount,url,abstract,openAccessPdf,externalIds",
    }
    with httpx.Client(timeout=6.0, follow_redirects=True) as client:
        resp = client.get("https://api.semanticscholar.org/graph/v1/paper/search", params=params)
        resp.raise_for_status()
        data = resp.json()
    results = []
    for paper in data.get("data", []):
        authors = ", ".join(a.get("name", "") for a in paper.get("authors", [])[:4] if a.get("name"))
        pdf = paper.get("openAccessPdf") or {}
        results.append({
            "title": _clean(paper.get("title", "")),
            "authors": authors,
            "year": paper.get("year") or "",
            "citationCount": paper.get("citationCount") or 0,
            "url": paper.get("url") or "",
            "openAccessUrl": pdf.get("url", "") if isinstance(pdf, dict) else "",
            "source": "semantic-scholar",
            "shortDesc": _clean(paper.get("abstract", ""))[:260],
        })
    return [item for item in results if item.get("title")]


def search_papers(query: str, limit: int = 8, external: bool = True) -> dict:
    query = _clean(query)
    limit = max(1, min(int(limit or 8), 20))
    if not query:
        return {"query": query, "papers": [], "sourceStatus": {"local": "skipped", "external": "skipped"}}

    papers = _local_paper_search(query, limit)
    status = {"local": f"{len(papers)} results", "openalex": "skipped", "semanticScholar": "skipped"}
    seen = {_paper_key(paper) for paper in papers}

    if external and len(papers) < limit:
        for name, fn in (("openalex", _openalex_search), ("semanticScholar", _semantic_scholar_search)):
            try:
                external_items = fn(query, limit - len(papers))
                status[name] = f"{len(external_items)} results"
                for paper in external_items:
                    key = _paper_key(paper)
                    if not key or key in seen:
                        continue
                    seen.add(key)
                    papers.append(paper)
                    if len(papers) >= limit:
                        break
            except Exception as exc:  # External search should never break local reading.
                status[name] = f"error: {type(exc).__name__}"
            if len(papers) >= limit:
                break

    return {"query": query, "papers": papers[:limit], "sourceStatus": status}


def evidence_snippets(question: str, paper_text: str, known_terms: list[dict], limit: int = 4) -> dict:
    question = _clean(question)
    chunks = [chunk.strip() for chunk in re.split(r"\n\s*\n|(?<=[.!?。！？])\s+", paper_text or "") if chunk.strip()]
    terms_in_question = [
        str(item.get("term", ""))
        for item in known_terms
        if isinstance(item, dict) and item.get("term") and item.get("term", "").lower() in question.lower()
    ]
    query_tokens = [token.lower() for token in re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}|[\u4e00-\u9fff]{2,}", question)]
    scored = []
    for idx, chunk in enumerate(chunks):
        lower = chunk.lower()
        score = sum(2 for term in terms_in_question if term.lower() in lower)
        score += sum(1 for token in query_tokens if token in lower)
        if score:
            scored.append((score, idx, chunk[:700]))
    scored.sort(key=lambda item: (-item[0], item[1]))
    snippets = [
        {"index": idx, "score": score, "text": text}
        for score, idx, text in scored[:limit]
    ]
    top_terms = Counter(terms_in_question).most_common(5)
    return {
        "question": question,
        "snippets": snippets,
        "terms": [name for name, _ in top_terms],
        "suggestedUse": "把这些证据片段交给右侧 AI 伴学，可以要求它只基于证据回答。",
    }
