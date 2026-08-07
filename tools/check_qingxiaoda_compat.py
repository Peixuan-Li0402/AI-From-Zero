#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import time

import httpx


def check(condition: bool, label: str, detail: str = "") -> None:
    if not condition:
        raise RuntimeError(f"{label}: {detail or 'failed'}")
    print(f"PASS {label}{f' - {detail}' if detail else ''}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe the Qingxiaoda OpenAI-compatible Agent endpoints.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8080/v1")
    parser.add_argument("--key", default=os.environ.get("QXD_API_KEY", ""))
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()
    if not args.key:
        raise SystemExit("Set QXD_API_KEY or pass --key. The key is never printed.")

    base = args.base_url.rstrip("/")
    if not base.endswith("/v1"):
        base += "/v1"
    headers = {"Authorization": f"Bearer {args.key}"}
    invalid_headers = {"Authorization": f"Bearer {args.key}-invalid"}

    with httpx.Client(timeout=args.timeout) as client:
        invalid = client.get(f"{base}/models", headers=invalid_headers)
        check(invalid.status_code == 401, "invalid-credential", f"HTTP {invalid.status_code}")

        models = client.get(f"{base}/models", headers=headers)
        check(models.status_code == 200, "models-status", f"HTTP {models.status_code}")
        model_data = models.json()
        check(bool(model_data.get("data")), "models-format")

        non_stream = client.post(
            f"{base}/chat/completions",
            headers=headers,
            json={"messages": [{"role": "user", "content": "解释 Transformer"}]},
        )
        check(non_stream.status_code == 200, "non-stream-status", f"HTTP {non_stream.status_code}")
        non_stream_data = non_stream.json()
        check(bool(non_stream_data.get("choices", [{}])[0].get("message", {}).get("content")), "non-stream-format")
        check("usage" in non_stream_data, "non-stream-usage")

        started = time.perf_counter()
        with client.stream(
            "POST",
            f"{base}/chat/completions",
            headers=headers,
            json={"stream": True, "max_tokens": 1, "messages": [{"role": "user", "content": "你好"}]},
        ) as response:
            check(response.status_code == 200, "stream-status", f"HTTP {response.status_code}")
            payloads = []
            done = False
            for line in response.iter_lines():
                if not line.startswith("data: "):
                    continue
                data = line[6:]
                if data == "[DONE]":
                    done = True
                    continue
                payloads.append(json.loads(data))
        elapsed = time.perf_counter() - started
        check(elapsed < 5.0, "minimal-chat-latency", f"{elapsed:.3f}s")
        check(bool(payloads and payloads[0]["choices"][0]["delta"].get("role") == "assistant"), "stream-role-frame")
        check(any(item["choices"][0]["delta"].get("content") for item in payloads), "stream-content-frame")
        stop_frames = [item for item in payloads if item["choices"][0].get("finish_reason")]
        check(bool(stop_frames and stop_frames[-1].get("usage")), "stream-stop-usage")
        check(done, "stream-done")

    print("Qingxiaoda compatibility probe passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
