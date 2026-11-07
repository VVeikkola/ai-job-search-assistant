from src.cv_analyzer import save_cv_analysis
from src.models import CVAnalysis


def test_save_cv_analysis_roundtrip(tmp_path):
    cv = CVAnalysis(
        name="Test Person",
        skills=["Python"],
        experience=["Developer at Example Oy"],
        languages=["English: Fluent"],
    )
    path = tmp_path / "nested" / "cv_analysis.json"

    save_cv_analysis(cv, path)

    assert CVAnalysis.model_validate_json(path.read_text("utf-8")) == cv
