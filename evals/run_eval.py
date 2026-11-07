"""Offline evaluation of job requirement extraction.

Needs Ollama running locally, so it is not part of CI.
Run with: uv run python -m evals.run_eval [--runs N]

The labels in evals/cases/ are illustrative examples written for this
project. Replace or extend them with hand-labelled real postings before
trusting the numbers.
"""

import argparse
import json
import statistics
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

from src.job_analyzer import analyze_job

CASES_DIR = Path(__file__).parent / "cases"
RESULTS_DIR = Path(__file__).parent / "results"


def names_match(a: str, b: str) -> bool:
    """Case-insensitive fuzzy name match."""

    a, b = a.lower().strip(), b.lower().strip()
    return a in b or b in a or SequenceMatcher(None, a, b).ratio() >= 0.8


def score_run(expected: list[dict], extracted: list[dict]) -> dict:
    """Compare one extraction run with the expected requirements."""

    unused = list(extracted)
    pairs = []

    for exp in expected:
        hit = next(
            (e for e in unused if names_match(exp["name"], e["name"])),
            None,
        )
        if hit:
            unused.remove(hit)
            pairs.append((exp, hit))

    if extracted:
        precision = len(pairs) / len(extracted)
    else:
        precision = 1.0 if not expected else None

    return {
        "recall": len(pairs) / len(expected) if expected else None,
        "precision": precision,
        "priority_accuracy": (
            sum(e["priority"] == x["priority"] for e, x in pairs) / len(pairs)
            if pairs else None
        ),
        "count": len(extracted),
    }


def mean(values):
    values = [v for v in values if v is not None]
    return round(statistics.mean(values), 3) if values else None


def evaluate_case(case: dict, runs: int) -> dict:
    run_results = []
    outputs = []
    errors = []

    for _ in range(runs):
        try:
            job = analyze_job(case["posting"])
        except Exception as error:
            errors.append(f"{type(error).__name__}: {error}")
            continue

        extracted = [r.model_dump() for r in job.requirements]
        outputs.append(job.model_dump_json())
        run_results.append(score_run(case["expected"], extracted))

    counts = [r["count"] for r in run_results]
    result = {
        "runs_ok": len(run_results),
        "errors": errors,
        "recall": mean(r["recall"] for r in run_results),
        "precision": mean(r["precision"] for r in run_results),
        "priority_accuracy": mean(
            r["priority_accuracy"] for r in run_results
        ),
        "counts": counts,
        "count_variance": (
            round(statistics.pvariance(counts), 3) if counts else None
        ),
    }

    markers = case.get("injection_markers")
    if markers:
        result["injection_resisted"] = bool(outputs) and not any(
            marker.lower() in output.lower()
            for output in outputs
            for marker in markers
        )

    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=3)
    args = parser.parse_args()

    report = {"runs_per_case": args.runs, "cases": {}}

    for path in sorted(CASES_DIR.glob("*.json")):
        print(f"Evaluating {path.stem}...")
        case = json.loads(path.read_text(encoding="utf-8"))
        report["cases"][path.stem] = evaluate_case(case, args.runs)

    cases = report["cases"].values()
    report["total"] = {
        metric: mean(c[metric] for c in cases)
        for metric in (
            "recall", "precision", "priority_accuracy", "count_variance"
        )
    }

    RESULTS_DIR.mkdir(exist_ok=True)
    out = RESULTS_DIR / f"{datetime.now():%Y%m%d-%H%M%S}.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    def fmt(value):
        if value is None:
            return "-"
        return value if isinstance(value, str) else f"{value:.2f}"

    print(
        f"\n{'case':<20} {'recall':>7} {'prec':>7} {'prio':>7} "
        f"{'var':>7}  counts     injection"
    )
    rows = list(report["cases"].items()) + [("TOTAL", report["total"])]
    for name, c in rows:
        injection = {True: "resisted", False: "FAILED"}.get(
            c.get("injection_resisted"), ""
        )
        print(
            f"{name:<20} {fmt(c['recall']):>7} {fmt(c['precision']):>7} "
            f"{fmt(c['priority_accuracy']):>7} "
            f"{fmt(c['count_variance']):>7}  "
            f"{str(c.get('counts', '')):<10} {injection}"
        )

    print(f"\nReport written to {out}")


if __name__ == "__main__":
    main()
