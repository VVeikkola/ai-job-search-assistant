import json
from pathlib import Path

from src.graph import graph
from src.job_fetcher import search_jobs
from src.models import CVAnalysis


CV_CACHE = Path("data/private/cv_analysis.json")
OUTPUT_FILE = Path("data/private/job_results.json")


def load_cv() -> CVAnalysis:
    """Load previously analyzed CV."""

    if not CV_CACHE.exists():
        raise FileNotFoundError(
            "CV analysis missing. Run: "
            "uv run python -m src.cv_analyzer"
        )

    return CVAnalysis.model_validate_json(
        CV_CACHE.read_text(encoding="utf-8")
    )


def save_results(results: list[dict]):
    """Save job matching results locally."""

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    OUTPUT_FILE.write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def main():
    print("Loading CV analysis...")
    cv = load_cv()

    print("\nFetching jobs...")
    jobs = search_jobs()

    print(f"Found {len(jobs)} jobs")

    results = []

    for job in jobs:

        print(f"\nAnalyzing: {job.title} — {job.company}")

        try:
            # LangGraph handles analysis, matching and scoring.
            state = graph.invoke({
                "job_text": (
                    f"Job title: {job.title}\n"
                    f"Company: {job.company}\n\n"
                    f"{job.description}"
                ),
                "cv": cv,
            })

            match = state["match"]
            score = match.score

            result = {
                "title": job.title,
                "company": job.company,
                "score": score,
                "decision": state["decision"],
                "reason": match.recommendation,
                "project_suggestion": state.get(
                    "project_suggestion"
                ),
                "url": job.url,
            }

            results.append(result)

            # Save after each successful analysis.
            save_results(results)

            print(f"Score: {score}/10")
            print(f"Decision: {state['decision']}")

            if result["project_suggestion"]:
                print(
                    "Project suggestion:",
                    result["project_suggestion"],
                )

        except Exception as error:
            print(f"Error analyzing {job.title}: {error}")

    results.sort(
        key=lambda result: (
            result["score"] is not None,
            result["score"]
            if result["score"] is not None
            else -1,
        ),
        reverse=True,
    )

    save_results(results)

    print("\nTOP JOB MATCHES")
    print("=" * 50)

    for result in results:

        print(
            f"\n{result['title']} — {result['company']}"
        )

        print(f"Score: {result['score']}/10")
        print(f"Decision: {result['decision']}")
        print(f"Reason: {result['reason']}")

        if result["project_suggestion"]:
            print(
                f"Project: {result['project_suggestion']}"
            )

        print(f"Apply: {result['url']}")


if __name__ == "__main__":
    main()