from __future__ import annotations

import argparse
import asyncio
import json
import random
import statistics
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.agent_core import generate_agent_response  # noqa: E402
from app.agent_runtime import route_agent_request  # noqa: E402
from app.config import settings  # noqa: E402
from app.models import QingxiaodaChatRequest  # noqa: E402
from app.terms import extract_terms_from_text  # noqa: E402

from check_agent_eval_split import validate_splits  # noqa: E402


def _load(name: str) -> list[dict]:
    path = ROOT / "evals" / f"agent_{name}.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


async def _evaluate_case(case: dict) -> tuple[list[str], float]:
    request = QingxiaodaChatRequest(messages=[{"role": "user", "content": case["question"]}])
    terms = extract_terms_from_text(case["question"])
    plan = route_agent_request(case["question"], has_documents=False, has_focus_term=bool(terms))
    failures = []
    if plan.intent != case["expected_intent"]:
        failures.append(f"intent={plan.intent}, expected={case['expected_intent']}")
    started = time.perf_counter()
    result = await generate_agent_response(request)
    elapsed_ms = (time.perf_counter() - started) * 1000
    for expected in case.get("must_contain", []):
        if expected.lower() not in result.content.lower():
            failures.append(f"missing={expected}")
    if elapsed_ms > float(case.get("max_latency_ms", 750)):
        failures.append(f"latency={elapsed_ms:.1f}ms")
    return failures, elapsed_ms


async def main(split: str, seed: int, variants: int) -> int:
    validate_splits()
    settings.agent_realtime_search = False
    settings.llm_api_key = ""
    settings.kimi_api_key = ""
    cases = _load(split)
    rng = random.Random(seed)
    rng.shuffle(cases)
    prefixes = ("", "请帮我看一下：", "我刚入门，")
    suffixes = ("", "，只说重点", "，可以保留双语术语")
    failures = []
    latencies = []
    for case in cases:
        for variant in range(variants):
            current = dict(case)
            if variant:
                current["question"] = f"{rng.choice(prefixes)}{case['question']}{rng.choice(suffixes)}"
            case_failures, elapsed_ms = await _evaluate_case(current)
            latencies.append(elapsed_ms)
            if case_failures:
                failures.append(f"{case['id']}[variant={variant}]: " + "; ".join(case_failures))
    if failures:
        print("FAIL agent eval")
        for failure in failures:
            print(f"- {failure}")
        return 1
    p95_index = max(0, int(len(latencies) * 0.95) - 1)
    ordered = sorted(latencies)
    print(
        f"PASS agent eval split={split} cases={len(cases)} variants={variants} seed={seed} "
        f"runs={len(latencies)} median={statistics.median(latencies):.1f}ms p95={ordered[p95_index]:.1f}ms"
    )
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=("train", "dev", "test", "test_round2"), default="dev")
    parser.add_argument("--seed", type=int, default=20260821)
    parser.add_argument("--variants", type=int, choices=range(1, 6), default=3)
    args = parser.parse_args()
    raise SystemExit(asyncio.run(main(args.split, args.seed, args.variants)))
