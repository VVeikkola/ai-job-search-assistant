from src.scoring import RequirementMatch, calculate_score


def test_skill_matching():
    requirements = [
        RequirementMatch(
            name="Python",
            priority="required",
            match="full",
            evidence="Python development experience"
        ),
        RequirementMatch(
            name="CI/CD",
            priority="required",
            match="partial",
            evidence="Jenkins experience"
        ),
        RequirementMatch(
            name="Azure",
            priority="required",
            match="unknown"
        )
    ]

    result = calculate_score(requirements)

    assert result["score"] == 5.0
    assert result["possible_score"] == 8.3
    assert result["unknown_requirements"] == ["Azure"]


def test_perfect_match():
    requirements = [
        RequirementMatch(
            name="Python",
            priority="required",
            match="full"
        )
    ]

    result = calculate_score(requirements)

    assert result["score"] == 10.0


def test_required_skills_have_higher_weight():
    requirements = [
        RequirementMatch(
            name="Python",
            priority="required",
            match="full"
        ),
        RequirementMatch(
            name="Azure",
            priority="preferred",
            match="not_met"
        )
    ]

    result = calculate_score(requirements)

    assert result["score"] == 7.5


def test_empty_requirements():
    result = calculate_score([])

    assert result["score"] is None

def _match(requirements):
    from src.models import MatchAnalysis

    return MatchAnalysis(
        matching_skills=[],
        missing_skills=[],
        recommendation="",
        score=0,
        score_reason="Pending Python scoring",
        requirements=requirements,
    )


def test_score_node_sets_possible_score_without_mutating_input():
    from src.graph import score_node

    original = _match([
        RequirementMatch(name="Python", priority="required", match="full"),
        RequirementMatch(name="Azure", priority="preferred", match="unknown"),
    ])

    update = score_node({"match": original})
    match = update["match"]

    assert match.score == 7.5
    assert match.possible_score == 10.0
    assert match.unknown_requirements == ["Azure"]
    assert update["decision"] == "Recommended to apply"

    assert match is not original
    assert original.score == 0
    assert original.possible_score is None


def test_score_node_without_requirements():
    from src.graph import score_node

    update = score_node({"match": _match([])})

    assert update["match"].score is None
    assert update["match"].possible_score is None
    assert update["decision"] == "Not enough information"
