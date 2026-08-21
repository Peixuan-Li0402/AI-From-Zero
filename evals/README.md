# Agent evaluation sets

- `agent_train.jsonl`: examples used to design intent and answer rubrics.
- `agent_dev.jsonl`: cases used while iterating locally.
- `agent_test.jsonl`: held-out acceptance cases. Runtime code and prompts must never import this file.
- `agent_test_round2.jsonl`: a second held-out set created after the first acceptance run exposed alias-display regressions.

All evaluation files use disjoint IDs, topics, and normalized questions. Run:

```bash
python tools/check_agent_eval_split.py
python tools/eval_agent_v2.py --split dev
python tools/eval_agent_v2.py --split test
python tools/eval_agent_v2.py --split test_round2
```

The evaluator disables external search and LLM calls. This makes routing, local knowledge retrieval, output contracts, and latency reproducible. Network and model quality are tested separately by protocol smoke tests.
