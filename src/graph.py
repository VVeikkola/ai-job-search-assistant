from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from src.job_analyzer import analyze_job
from src.match_analyzer import analyze_match
from src.models import CVAnalysis, JobAnalysis, MatchAnalysis
from src.scoring import calculate_score


class JobSearchState(TypedDict, total=False):
    job_text: str
    cv: CVAnalysis
    job: JobAnalysis
    match: MatchAnalysis
    decision: str
    project_suggestion: str


def job_node(state: JobSearchState):
    job = analyze_job(state["job_text"])
    return {"job": job}


def match_node(state: JobSearchState):
    match = analyze_match(state["job"], state["cv"])
    return {"match": match}


def score_node(state: JobSearchState):
    result = calculate_score(state["match"].requirements)
    score = result["score"]

    if score is None:
        decision = "Not enough information"
        score_reason = "No job requirements available for scoring."
    else:
        score_reason = (
            "Calculated using weighted job requirements. "
            "Required skills have weight 3 and preferred skills weight 1."
        )

        if score >= 7:
            decision = "Recommended to apply"
        elif score >= 5:
            decision = "Consider applying"
        else:
            decision = "Low priority"

    match = state["match"].model_copy(update={
        "score": score,
        "possible_score": result["possible_score"],
        "unknown_requirements": result["unknown_requirements"],
        "score_reason": score_reason,
    })

    return {
        "match": match,
        "decision": decision,
    }


def project_node(state: JobSearchState):
    missing_skills = state["match"].missing_skills

    if not missing_skills:
        suggestion = "No additional project needed."
    else:
        skills = ", ".join(missing_skills)

        suggestion = (
            f"Consider building a small portfolio project "
            f"demonstrating: {skills}"
        )

    return {"project_suggestion": suggestion}


def route_by_score(state: JobSearchState):
    score = state["match"].score

    if score is not None and score >= 5:
        return "project"

    return "end"


builder = StateGraph(JobSearchState)

builder.add_node("analyze_job", job_node)
builder.add_node("analyze_match", match_node)
builder.add_node("score", score_node)
builder.add_node("project", project_node)

builder.add_edge(START, "analyze_job")
builder.add_edge("analyze_job", "analyze_match")
builder.add_edge("analyze_match", "score")

builder.add_conditional_edges(
    "score",
    route_by_score,
    {
        "project": "project",
        "end": END,
    },
)

builder.add_edge("project", END)

graph = builder.compile()