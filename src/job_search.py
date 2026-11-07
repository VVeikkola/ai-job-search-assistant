import json
import logging
from pathlib import Path

from src.graph import graph
from src.job_fetcher import search_jobs
from src.models import CVAnalysis, JobPosting

CV_CACHE = Path("data/private/cv_analysis.json")
OUTPUT_FILE = Path("data/private/job_results.json")

logger = logging.getLogger(__name__)


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


def load_results() -> list[dict]:
    """Load earlier results. Entries without a job id cannot be
    matched, so they are dropped and those jobs are analyzed again."""

    if not OUTPUT_FILE.exists():
        return []

    results = json.loads(OUTPUT_FILE.read_text(encoding="utf-8"))

    return [result for result in results if result.get("id")]


def save_results(results: list[dict]):
    """Save job matching results locally."""

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    OUTPUT_FILE.write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def analyze(job: JobPosting, cv: CVAnalysis) -> dict | None:
    """Run the graph for one job and build its result entry.
    Logs and returns None if any step fails."""

    step = "start"

    try:
        # LangGraph handles analysis, matching and scoring.
        for mode, chunk in graph.stream(
            {
                "job_text": (
                    f"Job title: {job.title}\n"
                    f"Company: {job.company}\n\n"
                    f"{job.description}"
                ),
                "cv": cv,
            },
            stream_mode=["tasks", "values"],
        ):
            if mode == "tasks":
                step = chunk["name"]
            else:
                state = chunk

        step = "build_result"
        match = state["match"]

        return {
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "score": match.score,
            "possible_score": match.possible_score,
            "unknown_requirements": match.unknown_requirements,
            "decision": state["decision"],
            "reason": match.recommendation,
            "project_suggestion": state.get("project_suggestion"),
            "url": job.url,
        }

    except Exception as error:
        logger.error(
            "Job %s failed at %s: %s: %s",
            job.id,
            step,
            type(error).__name__,
            error,
        )
        return None


def process_jobs(
    jobs: list[JobPosting],
    cv: CVAnalysis,
    results: list[dict],
) -> list[dict]:
    """Analyze jobs not already in results. Failed jobs are logged
    and skipped so the rest of the batch still runs."""

    done = {result["id"] for result in results}
    new_jobs = [job for job in jobs if job.id not in done]

    print(f"{len(jobs) - len(new_jobs)} already analyzed, "
          f"{len(new_jobs)} new")

    for job in new_jobs:

        print(f"\nAnalyzing: {job.title} — {job.company}")

        result = analyze(job, cv)

        if result is None:
            continue

        results.append(result)

        # Save after each successful analysis.
        save_results(results)

        print(f"Score: {result['score']}/10")
        print(f"Possible score: {result['possible_score']}/10")
        print(f"Decision: {result['decision']}")

        if result["project_suggestion"]:
            print(
                "Project suggestion:",
                result["project_suggestion"],
            )

    return results


def main():
    logging.basicConfig(
        level=logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )

    print("Loading CV analysis...")
    cv = load_cv()

    print("\nFetching jobs...")
    jobs = search_jobs()

    print(f"Found {len(jobs)} jobs")

    results = process_jobs(jobs, cv, load_results())

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
        print(f"Possible score: {result['possible_score']}/10")

        if result["unknown_requirements"]:
            print(
                "Unknown: "
                + ", ".join(result["unknown_requirements"])
            )

        print(f"Decision: {result['decision']}")
        print(f"Reason: {result['reason']}")

        if result["project_suggestion"]:
            print(
                f"Project: {result['project_suggestion']}"
            )

        print(f"Apply: {result['url']}")


if __name__ == "__main__":
    main()
