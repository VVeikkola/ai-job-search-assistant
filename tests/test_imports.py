"""Smoke test: all modules import without Ollama or an API key."""

import importlib

import pytest

MODULES = [
    "src.graph",
    "src.job_search",
    "src.match_analyzer",
    "src.job_analyzer",
    "src.cv_analyzer",
]


@pytest.mark.parametrize("module", MODULES)
def test_module_imports(module, monkeypatch):
    # Point at an unreachable host so the test proves no connection is made.
    monkeypatch.setenv("OLLAMA_HOST", "http://127.0.0.1:1")
    importlib.import_module(module)
