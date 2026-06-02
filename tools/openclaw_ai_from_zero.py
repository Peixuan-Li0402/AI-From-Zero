#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import httpx


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def print_json(data: dict) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def request_json(method: str, base_url: str, path: str, **kwargs) -> dict:
    with httpx.Client(timeout=60.0) as client:
        resp = client.request(method, f"{base_url.rstrip('/')}{path}", **kwargs)
    try:
        data = resp.json()
    except ValueError:
        data = {"text": resp.text}
    if resp.status_code >= 400:
        raise RuntimeError(data.get("detail") or data.get("error") or f"HTTP {resp.status_code}")
    return data


def read_text_file(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="OpenClaw helper for AI-From-Zero.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8080")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("health")

    search = sub.add_parser("search-papers")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=5)
    search.add_argument("--no-external", action="store_true")

    load = sub.add_parser("load-paper")
    load.add_argument("title")
    load.add_argument("--url", default="")
    load.add_argument("--pdf-url", default="")

    analyze = sub.add_parser("analyze-text")
    analyze.add_argument("--file", required=True)
    analyze.add_argument("--title", default="")

    chat = sub.add_parser("chat")
    chat.add_argument("message")
    chat.add_argument("--paper-file", default="")
    chat.add_argument("--summary", default="")
    chat.add_argument("--local-only", action="store_true")

    args = parser.parse_args()
    try:
        if args.command == "health":
            print_json(request_json("GET", args.base_url, "/api/health"))
        elif args.command == "search-papers":
            print_json(request_json(
                "GET",
                args.base_url,
                "/api/papers/search",
                params={"query": args.query, "limit": args.limit, "external": not args.no_external},
            ))
        elif args.command == "load-paper":
            print_json(request_json(
                "POST",
                args.base_url,
                "/api/papers/load",
                json={"title": args.title, "url": args.url, "pdfUrl": args.pdf_url},
            ))
        elif args.command == "analyze-text":
            print_json(request_json(
                "POST",
                args.base_url,
                "/api/analyze",
                json={"title": args.title, "text": read_text_file(args.file)},
            ))
        elif args.command == "chat":
            paper_text = read_text_file(args.paper_file) if args.paper_file else ""
            print_json(request_json(
                "POST",
                args.base_url,
                "/api/chat",
                json={
                    "message": args.message,
                    "paperText": paper_text,
                    "paperSummary": args.summary,
                    "localOnly": args.local_only,
                },
            ))
    except Exception as exc:
        print_json({"error": str(exc)})
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
