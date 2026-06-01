#!/usr/bin/env python3
import argparse
import sys

import httpx


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test AI-From-Zero HTTP API.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8080")
    args = parser.parse_args()

    checks = []
    with httpx.Client(timeout=20) as client:
        health = client.get(f"{args.base_url}/api/health")
        checks.append(("health", health.status_code == 200 and health.json().get("status") == "ok" and health.json().get("llmProvider")))

        config = client.get(f"{args.base_url}/api/config")
        checks.append(("config", config.status_code == 200 and "maskedKey" in config.json()))

        text = "Transformer self-attention CNN RNN encoder decoder neural network model analysis text."
        analyze = client.post(f"{args.base_url}/api/analyze", json={"text": text})
        checks.append(("analyze", analyze.status_code == 200 and analyze.json().get("knownTerms")))

        term = client.get(f"{args.base_url}/api/terms/Transformer")
        checks.append(("term", term.status_code == 200 and term.json().get("term") == "Transformer"))

        papers = client.post(f"{args.base_url}/api/terms/Transformer/papers")
        checks.append(("papers", papers.status_code == 200 and papers.json().get("papers")))

        learn = client.post(f"{args.base_url}/api/learn-path", json={"interest": "llm"})
        checks.append(("learn-path", learn.status_code == 200 and learn.json().get("paths")))

        chat = client.post(f"{args.base_url}/api/chat", json={"message": "解释 Transformer", "knownTerms": [{"term": "Transformer"}]})
        checks.append(("chat", chat.status_code == 200 and chat.json().get("reply")))

    failed = [name for name, ok in checks if not ok]
    if failed:
        print("FAILED:", ", ".join(failed))
        return 1
    print("PASS:", ", ".join(name for name, _ in checks))
    return 0


if __name__ == "__main__":
    sys.exit(main())
