import logging

import src.graph
import src.job_search as job_search
from src.models import CVAnalysis, JobAnalysis, JobPosting, MatchAnalysis
from src.scoring import RequirementMatch

CV = CVAnalysis(name="Test", skills=["Python"], experience=[])


def make_job(job_id, description="Python developer"):
    return JobPosting(
        id=job_id,
        title=f"Job {job_id}",
        company="Example Oy",
        location="Oulu",
        description=description,
        url=f"https://example.com/{job_id}",
        source="test",
    )


def fake_analyze_job(job_text):
    if "BROKEN" in job_text:
        raise ValueError("bad model output")
    return JobAnalysis(company="Example Oy", position="Dev", requirements=[])


def fake_analyze_match(job, cv):
    return MatchAnalysis(
        matching_skills=["Python"],
        missing_skills=[],
        recommendation="Apply",
        score=0,
        score_reason="Pending Python scoring",
        requirements=[
            RequirementMatch(name="Python", priority="required", match="full")
        ],
    )


def test_process_jobs_skips_done_and_logs_failures(
    tmp_path, monkeypatch, caplog
):
    monkeypatch.setattr(src.graph, "analyze_job", fake_analyze_job)
    monkeypatch.setattr(src.graph, "analyze_match", fake_analyze_match)
    monkeypatch.setattr(job_search, "OUTPUT_FILE", tmp_path / "results.json")

    jobs = [make_job("1"), make_job("2", "BROKEN"), make_job("3")]
    existing = [{"id": "1", "score": 9.0}]

    with caplog.at_level(logging.ERROR):
        results = job_search.process_jobs(jobs, CV, existing)

    assert [r["id"] for r in results] == ["1", "3"]
    assert results[1]["score"] == 10.0
    assert results[1]["possible_score"] == 10.0
    assert "Job 2 failed at analyze_job: ValueError" in caplog.text

    assert [r["id"] for r in job_search.load_results()] == ["1", "3"]
