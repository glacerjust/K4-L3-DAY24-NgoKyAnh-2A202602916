"""Test bonus: Đánh giá và so sánh định lượng Regex vs GLiNER (Zero-shot NER)."""
from __future__ import annotations

import json
from pathlib import Path
from agent import pii

TESTSET_PATH = Path(__file__).resolve().parent / "vn_pii_testset.jsonl"


def test_regex_baseline_metrics_for_comparison():
    with TESTSET_PATH.open(encoding="utf-8") as f:
        testset = [json.loads(line) for line in f if line.strip()]

    total_gold = sum(len(row["entities"]) for row in testset)
    total_pred = 0
    tp = 0

    for row in testset:
        pred = pii.detect(row["text"])
        total_pred += len(pred)
        gold = row["entities"]
        for p in pred:
            for g in gold:
                if p["type"] == g["type"] and p["start"] < g["end"] and g["start"] < p["end"]:
                    tp += 1
                    break

    precision = tp / total_pred if total_pred else 0.0
    recall = tp / total_gold if total_gold else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    assert recall >= 0.95, "Regex baseline phải đạt recall >= 95%"
    assert precision >= 0.95, "Regex baseline phải đạt precision >= 95%"
    print(f"\n[Bonus Comparison] Regex F1={f1:.4f}, Precision={precision:.4f}, Recall={recall:.4f}")
