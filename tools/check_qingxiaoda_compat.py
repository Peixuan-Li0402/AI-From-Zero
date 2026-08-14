#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ipaddress
import json
import os
import socket
import time
from urllib.parse import urlparse

import httpx


def check(condition: bool, label: str, detail: str = "") -> None:
    if not condition:
        raise RuntimeError(f"{label}: {detail or 'failed'}")
    print(f"PASS {label}{f' - {detail}' if detail else ''}")


def resolved_addresses(base: str) -> set[str]:
    parsed = urlparse(base)
    if not parsed.hostname:
        raise RuntimeError("base-url: missing hostname")
    if parsed.hostname in {"127.0.0.1", "localhost", "::1"}:
        return {parsed.hostname}
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    return {item[4][0] for item in socket.getaddrinfo(parsed.hostname, port, type=socket.SOCK_STREAM)}


def validate_network_evidence(base: str, allow_proxy_evidence: bool) -> None:
    addresses = resolved_addresses(base)
    local = addresses <= {"127.0.0.1", "localhost", "::1"}
    non_public = []
    if not local:
        for value in addresses:
            try:
                if not ipaddress.ip_address(value.split("%", 1)[0]).is_global:
                    non_public.append(value)
            except ValueError:
                non_public.append(value)
    if non_public and not allow_proxy_evidence:
        raise RuntimeError(
            "network-evidence: DNS returned a non-public/fake IP "
            f"({', '.join(sorted(non_public))}). Disable the proxy/VPN or run from the deployment region; "
            "otherwise a passing result does not prove Qingxiaoda can connect directly."
        )
    label = "local target" if local else ", ".join(sorted(addresses))
    check(True, "network-evidence", label)


def parse_sse(response: httpx.Response) -> tuple[list[dict], bool]:
    payloads: list[dict] = []
    done = False
    for line in response.iter_lines():
        if not line.startswith("data: "):
            continue
        data = line[6:]
        if data == "[DONE]":
            done = True
        else:
            payloads.append(json.loads(data))
    return payloads, done


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the official Qingxiaoda OpenAI-compatible probe contract.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8080/v1")
    parser.add_argument("--key", default=os.environ.get("QXD_API_KEY", ""))
    parser.add_argument("--timeout", type=float, default=5.0, help="Per-item platform probe timeout.")
    parser.add_argument("--allow-proxy-evidence", action="store_true")
    parser.add_argument("--full-chat", action="store_true", help="Also run a real, potentially slow model reply.")
    parser.add_argument("--full-chat-timeout", type=float, default=120.0)
    args = parser.parse_args()
    if not args.key:
        raise SystemExit("Set QXD_API_KEY or pass --key. The key is never printed.")

    base = args.base_url.rstrip("/")
    if not base.endswith("/v1"):
        raise SystemExit("--base-url must end with /v1 exactly as entered in Qingxiaoda.")
    validate_network_evidence(base, args.allow_proxy_evidence)

    headers = {"Authorization": f"Bearer {args.key}"}
    invalid_headers = {"Authorization": f"Bearer {args.key}-invalid"}
    timeout = httpx.Timeout(args.timeout)
    probe_started = time.perf_counter()

    with httpx.Client(timeout=timeout, trust_env=False) as client:
        started = time.perf_counter()
        models = client.get(f"{base}/models", headers=headers)
        models_elapsed = time.perf_counter() - started
        check(models_elapsed < args.timeout, "connectivity-latency", f"{models_elapsed:.3f}s")
        check(models.status_code == 200, "models-status", f"HTTP {models.status_code}")
        model_data = models.json()
        check(bool(model_data.get("data")), "models-format")

        invalid = client.get(f"{base}/models", headers=invalid_headers)
        check(invalid.status_code == 401, "invalid-credential", f"HTTP {invalid.status_code}")

        started = time.perf_counter()
        with client.stream(
            "POST",
            f"{base}/chat/completions",
            headers=headers,
            json={"stream": True, "max_tokens": 1, "messages": [{"role": "user", "content": "probe"}]},
        ) as response:
            check(response.status_code == 200, "minimal-chat-status", f"HTTP {response.status_code}")
            payloads, done = parse_sse(response)
        minimal_elapsed = time.perf_counter() - started
        check(minimal_elapsed < args.timeout, "minimal-chat-latency", f"{minimal_elapsed:.3f}s")
        check(bool(payloads and payloads[0]["choices"][0]["delta"] == {"role": "assistant"}), "stream-role-frame")
        check(any(item["choices"][0]["delta"].get("content") for item in payloads), "stream-content-frame")
        stop_frames = [item for item in payloads if item["choices"][0].get("finish_reason")]
        check(len(stop_frames) == 1, "single-stop-frame")
        check(stop_frames[0]["choices"][0]["finish_reason"] == "stop", "finish-reason")
        check(stop_frames[0]["choices"][0]["delta"] == {}, "empty-stop-delta")
        check("usage" in stop_frames[0], "stream-stop-usage")
        check(done, "stream-done")

    total_elapsed = time.perf_counter() - probe_started
    check(total_elapsed < 15.0, "whole-probe-latency", f"{total_elapsed:.3f}s")

    if args.full_chat:
        with httpx.Client(timeout=args.full_chat_timeout, trust_env=False) as client:
            started = time.perf_counter()
            response = client.post(
                f"{base}/chat/completions",
                headers=headers,
                json={"messages": [{"role": "user", "content": "用两句话解释 Transformer。"}]},
            )
            elapsed = time.perf_counter() - started
            check(response.status_code == 200, "full-chat-status", f"HTTP {response.status_code}")
            data = response.json()
            check(bool(data.get("choices", [{}])[0].get("message", {}).get("content")), "full-chat-format")
            check("usage" in data, "full-chat-usage")
            check(elapsed < 120.0, "full-chat-latency", f"{elapsed:.3f}s")

    print("Qingxiaoda official compatibility probe passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, httpx.HTTPError, OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"FAIL {exc}") from None
