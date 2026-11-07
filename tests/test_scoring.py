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