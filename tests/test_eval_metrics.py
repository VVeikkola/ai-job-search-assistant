from evals.run_eval import names_match, score_run


def test_names_match_is_fuzzy_and_case_insensitive():
    assert names_match("PostgreSQL", "postgresql database")
    assert names_match("Kubernetes", "kubernetes")
    assert not names_match("Java", "Python")


def test_score_run():
    expected = [
        {"name": "Python", "priority": "required"},
        {"name": "Docker", "priority": "preferred"},
    ]
    extracted = [
        {"name": "python", "priority": "required"},
        {"name": "Docker", "priority": "required"},
        {"name": "Invented", "priority": "required"},
    ]

    result = score_run(expected, extracted)

    assert result["recall"] == 1.0
    assert result["precision"] == 2 / 3
    assert result["priority_accuracy"] == 0.5
    assert result["count"] == 3


def test_score_run_empty_posting():
    assert score_run([], [])["precision"] == 1.0
    assert score_run([], [{"name": "X", "priority": "required"}])["precision"] == 0.0
