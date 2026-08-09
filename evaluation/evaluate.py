"""
evaluation/evaluate.py

Evaluation harness for the dark pattern detection pipeline.

Measures per-category and overall precision, recall, and F1 score
against a manually labelled ground truth dataset.

Evaluation methodology:
  - For each URL, the system predicts a set of category IDs (e.g. {DP-4, DP-6})
  - Ground truth is a manually labelled set of expected category IDs
  - A True Positive (TP) is a category correctly detected
  - A False Positive (FP) is a category detected that is not in ground truth
  - A False Negative (FN) is a category in ground truth that was not detected
  - Precision = TP / (TP + FP)
  - Recall    = TP / (TP + FN)
  - F1        = 2 * (P * R) / (P + R)

Run from project root:
    python -m evaluation.evaluate

Results saved to:
    data/results/evaluation_report.json
    data/results/evaluation_summary.txt
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scraper.fetch import scrape
from detection_engine.engine import analyse

# ── Paths ─────────────────────────────────────────────────────────────────────

GROUND_TRUTH_PATH = Path(__file__).parent / "ground_truth.json"
RESULTS_DIR       = Path(__file__).parent.parent / "data" / "results"
REPORT_JSON       = RESULTS_DIR / "evaluation_report.json"
REPORT_TXT        = RESULTS_DIR / "evaluation_summary.txt"

ALL_CATEGORIES = ["DP-1", "DP-2", "DP-3", "DP-4", "DP-5", "DP-6"]

CATEGORY_NAMES = {
    "DP-1": "Misdirection",
    "DP-2": "Hidden Costs",
    "DP-3": "Confirmshaming",
    "DP-4": "Disguised Ads",
    "DP-5": "Forced Continuity",
    "DP-6": "Urgency / Scarcity",
}

# ── Metrics ───────────────────────────────────────────────────────────────────

def precision(tp: int, fp: int) -> float:
    return tp / (tp + fp) if (tp + fp) > 0 else 0.0

def recall(tp: int, fn: int) -> float:
    return tp / (tp + fn) if (tp + fn) > 0 else 0.0

def f1(p: float, r: float) -> float:
    return 2 * p * r / (p + r) if (p + r) > 0 else 0.0


# ── Per-URL evaluation ────────────────────────────────────────────────────────

async def evaluate_url(url: str, expected: list[str], notes: str) -> dict:
    """Scrape and analyse one URL, compare to ground truth."""
    t0 = time.monotonic()

    try:
        page = await scrape(url, timeout_ms=30000)
    except Exception as e:
        return {
            "url": url, "notes": notes,
            "expected": expected, "predicted": [],
            "tp": [], "fp": [], "fn": expected,
            "error": str(e),
            "elapsed": round(time.monotonic() - t0, 2),
        }

    if page.error:
        return {
            "url": url, "notes": notes,
            "expected": expected, "predicted": [],
            "tp": [], "fp": [], "fn": expected,
            "error": page.error,
            "elapsed": round(time.monotonic() - t0, 2),
        }

    try:
        result = analyse(page)
    except Exception as e:
        return {
            "url": url, "notes": notes,
            "expected": expected, "predicted": [],
            "tp": [], "fp": [], "fn": expected,
            "error": f"Engine error: {e}",
            "elapsed": round(time.monotonic() - t0, 2),
        }

    predicted = [f["id"] for f in result.get("findings", [])]
    expected_set  = set(expected)
    predicted_set = set(predicted)

    tp = sorted(expected_set & predicted_set)
    fp = sorted(predicted_set - expected_set)
    fn = sorted(expected_set - predicted_set)

    return {
        "url":       url,
        "notes":     notes,
        "expected":  sorted(expected),
        "predicted": sorted(predicted),
        "tp":        tp,
        "fp":        fp,
        "fn":        fn,
        "error":     None,
        "elapsed":   round(time.monotonic() - t0, 2),
        "findings":  result.get("findings", []),
    }


# ── Aggregate metrics ─────────────────────────────────────────────────────────

def compute_metrics(results: list[dict]) -> dict:
    """Compute per-category and overall precision/recall/F1."""

    # Overall counts across all URLs
    total_tp = total_fp = total_fn = 0

    # Per-category counts
    cat_tp = defaultdict(int)
    cat_fp = defaultdict(int)
    cat_fn = defaultdict(int)

    successful = [r for r in results if not r.get("error")]

    for r in successful:
        total_tp += len(r["tp"])
        total_fp += len(r["fp"])
        total_fn += len(r["fn"])

        for cat in r["tp"]: cat_tp[cat] += 1
        for cat in r["fp"]: cat_fp[cat] += 1
        for cat in r["fn"]: cat_fn[cat] += 1

    # Overall metrics
    overall_p  = precision(total_tp, total_fp)
    overall_r  = recall(total_tp, total_fn)
    overall_f1 = f1(overall_p, overall_r)

    # Per-category metrics
    per_category = {}
    for cat in ALL_CATEGORIES:
        p = precision(cat_tp[cat], cat_fp[cat])
        r = recall(cat_tp[cat], cat_fn[cat])
        per_category[cat] = {
            "name":      CATEGORY_NAMES[cat],
            "tp":        cat_tp[cat],
            "fp":        cat_fp[cat],
            "fn":        cat_fn[cat],
            "precision": round(p, 3),
            "recall":    round(r, 3),
            "f1":        round(f1(p, r), 3),
        }

    # Accuracy on negative examples (sites with no expected patterns)
    negatives = [r for r in successful if not r["expected"]]
    true_negatives  = sum(1 for r in negatives if not r["predicted"])
    false_positives_on_neg = sum(1 for r in negatives if r["predicted"])

    return {
        "total_urls":       len(results),
        "successful":       len(successful),
        "errors":           len(results) - len(successful),
        "overall": {
            "tp":        total_tp,
            "fp":        total_fp,
            "fn":        total_fn,
            "precision": round(overall_p, 3),
            "recall":    round(overall_r, 3),
            "f1":        round(overall_f1, 3),
        },
        "per_category":     per_category,
        "negative_sites": {
            "total":           len(negatives),
            "true_negatives":  true_negatives,
            "false_positives": false_positives_on_neg,
            "specificity":     round(true_negatives / len(negatives), 3) if negatives else 0.0,
        },
    }


# ── Report formatting ─────────────────────────────────────────────────────────

BOLD  = "\033[1m"
GREEN = "\033[92m"
RED   = "\033[91m"
AMBER = "\033[93m"
RESET = "\033[0m"

def colour_score(score: float) -> str:
    if score >= 0.70: return f"{GREEN}{score:.3f}{RESET}"
    if score >= 0.50: return f"{AMBER}{score:.3f}{RESET}"
    return f"{RED}{score:.3f}{RESET}"

def print_report(metrics: dict, results: list[dict]):
    print("\n" + "═" * 70)
    print(f"{BOLD}EVALUATION REPORT — Dark Pattern Detection Tool{RESET}")
    print(f"Run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("═" * 70)

    o = metrics["overall"]
    print(f"\n{BOLD}Overall Performance{RESET}")
    print(f"  URLs tested:   {metrics['total_urls']} ({metrics['successful']} successful, {metrics['errors']} errors)")
    print(f"  Precision:     {colour_score(o['precision'])}  (TP={o['tp']}, FP={o['fp']})")
    print(f"  Recall:        {colour_score(o['recall'])}  (TP={o['tp']}, FN={o['fn']})")
    print(f"  F1 score:      {colour_score(o['f1'])}")

    neg = metrics["negative_sites"]
    print(f"\n{BOLD}Specificity (negative sites){RESET}")
    print(f"  Clean sites tested:   {neg['total']}")
    print(f"  Correctly returned 0: {neg['true_negatives']}")
    print(f"  False positives:      {neg['false_positives']}")
    print(f"  Specificity:          {colour_score(neg['specificity'])}")

    print(f"\n{BOLD}Per-Category Results{RESET}")
    print(f"  {'Category':<25} {'P':>6} {'R':>6} {'F1':>6}  {'TP':>3} {'FP':>3} {'FN':>3}")
    print("  " + "-" * 58)
    for cat_id, cat in metrics["per_category"].items():
        support = cat["tp"] + cat["fn"]
        if support == 0 and cat["fp"] == 0:
            row = f"  {cat['name']:<25} {'—':>6} {'—':>6} {'—':>6}  {'—':>3} {'—':>3} {'—':>3}  (not in eval set)"
        else:
            row = (f"  {cat['name']:<25} "
                   f"{colour_score(cat['precision']):>6} "
                   f"{colour_score(cat['recall']):>6} "
                   f"{colour_score(cat['f1']):>6}  "
                   f"{cat['tp']:>3} {cat['fp']:>3} {cat['fn']:>3}")
        print(row)

    print(f"\n{BOLD}Per-URL Results{RESET}")
    print(f"  {'URL':<40} {'Expected':<15} {'Predicted':<15} {'TP':>3} {'FP':>3} {'FN':>3}")
    print("  " + "-" * 85)
    for r in results:
        if r.get("error"):
            print(f"  {r['url']:<40} ERROR: {r['error'][:40]}")
            continue
        expected_str  = ",".join(r["expected"])  or "none"
        predicted_str = ",".join(r["predicted"]) or "none"
        status = "✓" if not r["fp"] and not r["fn"] else "✗"
        print(f"  {status} {r['url'][:38]:<38} {expected_str:<15} {predicted_str:<15} "
              f"{len(r['tp']):>3} {len(r['fp']):>3} {len(r['fn']):>3}")

    print("\n" + "═" * 70)


def write_text_report(metrics: dict, results: list[dict]) -> str:
    """Write a plain-text report suitable for the dissertation appendix."""
    lines = []
    lines.append("EVALUATION REPORT — Automated Dark Pattern Detection Tool")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 60)

    o = metrics["overall"]
    lines.append("\nOVERALL METRICS")
    lines.append(f"  URLs tested:  {metrics['total_urls']}")
    lines.append(f"  Precision:    {o['precision']:.3f}")
    lines.append(f"  Recall:       {o['recall']:.3f}")
    lines.append(f"  F1 score:     {o['f1']:.3f}")
    lines.append(f"  TP={o['tp']}, FP={o['fp']}, FN={o['fn']}")

    neg = metrics["negative_sites"]
    lines.append(f"\nSPECIFICITY")
    lines.append(f"  Clean sites: {neg['total']}, Correct: {neg['true_negatives']}, FP: {neg['false_positives']}")
    lines.append(f"  Specificity: {neg['specificity']:.3f}")

    lines.append("\nPER-CATEGORY RESULTS")
    lines.append(f"  {'Category':<25} {'P':>6} {'R':>6} {'F1':>6} {'TP':>4} {'FP':>4} {'FN':>4}")
    lines.append("  " + "-" * 58)
    for cat_id, cat in metrics["per_category"].items():
        lines.append(f"  {cat['name']:<25} {cat['precision']:>6.3f} {cat['recall']:>6.3f} {cat['f1']:>6.3f} {cat['tp']:>4} {cat['fp']:>4} {cat['fn']:>4}")

    lines.append("\nPER-URL RESULTS")
    for r in results:
        lines.append(f"\n  URL: {r['url']}")
        lines.append(f"  Notes: {r['notes']}")
        if r.get("error"):
            lines.append(f"  ERROR: {r['error']}")
        else:
            lines.append(f"  Expected:  {r['expected'] or 'none'}")
            lines.append(f"  Predicted: {r['predicted'] or 'none'}")
            lines.append(f"  TP={r['tp']}, FP={r['fp']}, FN={r['fn']}")

    return "\n".join(lines)


# ── Main ──────────────────────────────────────────────────────────────────────

async def main():
    print(f"\n{BOLD}Loading ground truth from {GROUND_TRUTH_PATH}{RESET}")
    with open(GROUND_TRUTH_PATH, encoding="utf-8") as f:
        ground_truth = json.load(f)

    print(f"Evaluating {len(ground_truth)} URLs...\n")

    results = []
    for i, entry in enumerate(ground_truth, 1):
        url      = entry["url"]
        expected = entry.get("expected", [])
        notes    = entry.get("notes", "")

        print(f"[{i}/{len(ground_truth)}] {url}")
        result = await evaluate_url(url, expected, notes)

        status = "ERROR" if result.get("error") else (
            "✓" if not result["fp"] and not result["fn"] else
            f"FP={result['fp']} FN={result['fn']}"
        )
        print(f"  Expected: {expected or 'none'} | Predicted: {result['predicted'] or 'none'} | {status}")
        results.append(result)
        await asyncio.sleep(2)

    metrics = compute_metrics(results)
    print_report(metrics, results)

    # Save JSON report
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "metrics":      metrics,
        "results":      results,
    }
    with open(REPORT_JSON, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"JSON report saved to: {REPORT_JSON}")

    # Save text report
    txt = write_text_report(metrics, results)
    with open(REPORT_TXT, "w", encoding="utf-8") as f:
        f.write(txt)
    print(f"Text report saved to: {REPORT_TXT}")


if __name__ == "__main__":
    asyncio.run(main())
