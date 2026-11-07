from typing import Literal

from pydantic import BaseModel


class RequirementMatch(BaseModel):
    name: str
    priority: Literal["required", "preferred"]
    match: Literal["full", "partial", "not_met", "unknown"]
    evidence: str | None = None


def calculate_score(requirements: list[RequirementMatch]) -> dict:

    weights = {
        "required": 3,
        "preferred": 1,
    }

    match_values = {
        "full": 1.0,
        "partial": 0.5,
        "not_met": 0.0,
        "unknown": 0.0,
    }

    if not requirements:
        return {
            "score": None,
            "possible_score": None,
            "unknown_requirements": [],
        }

    total_weight = sum(
        weights[r.priority] for r in requirements
    )

    earned_points = sum(
        weights[r.priority] * match_values[r.match]
        for r in requirements
    )

    unknown = [
        r for r in requirements
        if r.match == "unknown"
    ]

    unknown_weight = sum(
        weights[r.priority] for r in unknown
    )

    return {
        "score": round(10 * earned_points / total_weight, 1),
        "possible_score": round(
            10 * (earned_points + unknown_weight) / total_weight, 1
        ),
        "unknown_requirements": [r.name for r in unknown],
    }