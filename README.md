# AI Job Search Assistant

[![CI](https://github.com/VVeikkola/ai-job-search-assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/VVeikkola/ai-job-search-assistant/actions/workflows/ci.yml)

A local, privacy-conscious job-search assistant built with **Python, LangGraph, Ollama, and Qwen**. It fetches job postings through the Headcount Labs API, compares their requirements with a structured CV profile, assigns an explainable suitability score, and suggests areas for portfolio development.

> **Project status:** Working local prototype. Scores are advisory, not predictions of hiring decisions.

## Features

- **Automated job discovery:** Searches for software, AI, data, and automation roles in Oulu and remote roles listed for Finland using Headcount Labs.
- **Structured CV analysis:** Uses a local LLM to extract skills, professional experience, education, projects, evidence of skills, and language proficiency.
- **CV analysis cache:** Saves the structured CV to a private local JSON file, avoiding repeated CV extraction on every search.
- **Structured job requirements:** Extracts each requirement with a priority (`required` or `preferred`) and a category (`technical`, `experience`, `language`, `education`, `other`), including language, experience and seniority requirements.
- **Job-to-CV matching:** Evaluates job requirements with evidence-based categories (`full`, `partial`, `not_met`, `unknown`) and priorities (`required`, `preferred`).
- **Deterministic scoring:** Python calculates a score from 0 to 10. Required requirements carry weight **3**, preferred requirements weight **1**; full matches earn full weight and partial matches half weight. A `possible_score` shows what the score would be if every `unknown` requirement were met.
- **LangGraph workflow:** Runs job analysis, matching, scoring, and conditional routing.
- **Project suggestions:** For scores of **5/10 or higher**, the workflow produces a basic suggestion based on skills that are not fully demonstrated, when applicable.
- **Local results:** Saves the analyzed job list to JSON, including job ids, scores, possible scores, unknown requirements, recommendations, suggestions, and application URLs. Reruns skip jobs that are already in the results file.
- **Offline evaluation:** A small harness measures how accurately and consistently the job requirements are extracted.

## Architecture

```text
                data/private/cv.txt
                        |
                        v
                 CV Analysis (Qwen)
                        |
                        v
             cv_analysis.json (Cache)
                        |
                        |
                        v
Headcount Labs API --> job_fetcher.py
                            |
                            v
                        job_search.py
                            |
                            v
                      LangGraph
                            |
                            v
                    Analyze Job (Qwen)
                            |
                            v
                 Match Job with Cached CV
                            |
                            v
                  Calculate Score (Python)
                            |
                            v
                       Score >= 5?
                       /        \
                     Yes         No
                      |           |
                      v           |
               Project Suggestion |
                      |           |
                      +-----+-----+
                            |
                            v
                       Final Result
                            |
                            v
                data/private/job_results.json
```

The LLM extracts and assesses evidence; **Python calculates the final numeric score**. LangGraph orchestrates each job evaluation. The job-search entry point retrieves a batch of postings and invokes the graph for each job.

## Tech stack

| Area | Technology |
| --- | --- |
| Language | Python |
| Workflow orchestration | LangGraph |
| LLM integration | LangChain / `langchain-ollama` |
| Local model | Ollama, `qwen3.5:9b` |
| Data validation | Pydantic |
| Job listings | Headcount Labs REST API |
| HTTP client | HTTPX |
| Environment configuration | `python-dotenv` |
| Dependency management | `uv` |
| Testing | pytest |



## Getting started

### Prerequisites

- Python environment managed with [`uv`](https://docs.astral.sh/uv/)
- [Ollama](https://ollama.com/) running locally
- The local `qwen3.5:9b` model
- A Headcount Labs API key

Start Ollama if needed and pull the model:

```bash
ollama pull qwen3.5:9b
```

Install the Python dependencies from the project directory:

```bash
uv sync
```

Create a `.env` file in the project root:

```dotenv
HEADCOUNTLABS_API_KEY=your_api_key_here
```

**Never commit `.env`, your CV, or generated private analysis files.** Confirm that `.gitignore` contains at least:

```gitignore
.env
data/private/
```

### 1. Add your CV profile

Save your CV as plain text at:

```text
data/private/cv.txt
```

Include factual skills, professional roles, projects, education, and languages. Only include personal information you are comfortable storing on your own machine.

### 2. Generate the CV analysis cache

```bash
uv run python -m src.cv_analyzer
```

This creates:

```text
data/private/cv_analysis.json
```

**Run this command again whenever you update `cv.txt`.** The search command reads the cached analysis instead of re-analyzing the CV every time.

### 3. Check job discovery

```bash
uv run python -m src.job_fetcher
```

### 4. Run the complete search and matching workflow

```bash
uv run python -m src.job_search
```

The command loads the cached CV, retrieves job postings, invokes LangGraph to evaluate each selected job, prints the ranked matches, and writes results to:

```text
data/private/job_results.json
```

> **Reruns:** Jobs whose id is already in `job_results.json` are skipped, so an interrupted run can be resumed. Delete the file to re-analyze everything. If one job fails, the error is logged with the job id and the failed step, and the remaining jobs keep processing. The API fetcher retrieves a limited number of results per search; full pagination has not yet been implemented.

### Run the tests and linter

```bash
uv run python -m pytest -q
uv run ruff check .
```

The tests do not need Ollama or an API key. GitHub Actions runs both commands on every push and pull request.

### Run the extraction evaluation

Requires Ollama running locally, so it is not part of CI:

```bash
uv run python -m evals.run_eval            # 3 runs per case
uv run python -m evals.run_eval --runs 5
```

Each file in `evals/cases/` holds a job posting and its expected requirements (name and priority). The harness runs the job analyzer on every case several times and reports, per case and in total:

- **Recall / precision:** share of expected requirements found, and share of extracted requirements that were expected (case-insensitive fuzzy name match).
- **Priority accuracy:** share of matched requirements with the correct `required` / `preferred` priority.
- **Count variance:** run-to-run variance in the number of extracted requirements.
- **Injection resisted:** for the prompt-injection case, whether any injected text appears in the output.

The cases include three example postings and three failure scenarios: a near-empty posting, a posting with a prompt-injection line, and a posting in Finnish. A JSON report is written to `evals/results/` (gitignored).

> **About the evals:** The evaluation step was added on a suggestion from Claude Code (Anthropic's AI coding assistant), which I used during development. Claude implemented the harness and the example cases, and I integrated them into the project as a way to measure extraction quality instead of judging it by eye.
>
> The example postings and labels are illustrative. Six short cases say little about real-world accuracy, so the next step is to extend the set with hand-labelled real job postings.

## How matching and scoring work

The job evaluator assigns each extracted requirement:

- **Priority:** `required` (weight 3) or `preferred` (weight 1).
- **Match:** `full` (100% credit), `partial` (50%), `not_met` (0%), or `unknown` (0% in the current score).

Priorities come from the job extraction step, where wording such as "must have" or "we expect" marks a requirement as required, and "nice to have", "we value" or "plus" marks it as preferred. The matching step copies these priorities instead of guessing them.

The weighted score is scaled to **0–10**. A requirement without evidence is classified as `unknown`, rather than being treated as proof that the candidate lacks the skill. Unknowns contribute no points to `score`, so it can underestimate a candidate whose CV omits relevant information. `possible_score` counts every unknown as a full match and gives the upper bound; the gap between the two shows how much depends on missing information. Unknown requirements are listed in the results.

| Score | Decision | Project suggestion |
| --- | --- | --- |
| 7.0–10.0 | Recommended to apply | When useful |
| 5.0–6.9 | Consider applying | When useful |
| Below 5.0 | Low priority | Not generated |
| No scorable requirements | Not enough information | Not generated |

The current project suggestion is a short, rule-based message listing missing skills, **not** a generated implementation plan.

## Project structure

```text
ai-job-search-assistant/
├── .github/workflows/
│   └── ci.yml              # Ruff and pytest on push / pull request
├── evals/
│   ├── cases/              # Example postings with expected requirements
│   └── run_eval.py         # Offline extraction evaluation (needs Ollama)
├── scripts/
│   └── check_api.py        # Manual Headcount Labs API smoke check
├── src/
│   ├── models.py           # Pydantic CV, job, and match models
│   ├── cv_analyzer.py      # Local CV extraction and cache saving
│   ├── job_fetcher.py      # Headcount Labs API and job filtering
│   ├── job_analyzer.py     # Job requirement extraction
│   ├── match_analyzer.py   # Evidence-based requirement matching
│   ├── scoring.py          # Deterministic weighted scoring
│   ├── graph.py            # LangGraph matching workflow
│   └── job_search.py       # Search entry point and result storage
├── tests/                  # Unit tests (no Ollama needed)
├── data/
│   └── private/            # Local CV and generated results (gitignored)
├── .env                   # API key (gitignored)
├── pyproject.toml
└── README.md
```

## Privacy and security

- CV analysis and LLM inference run locally through Ollama.
- Headcount Labs receives job-search requests and API credentials, **not the CV**, in the current workflow.
- The CV, cached analysis, and matching results are stored under `data/private/` and should be excluded from version control.
- Job postings and their descriptions are external, untrusted content. The job analyzer wraps the posting in `<job_posting>` delimiters and tells the model to ignore instructions inside it; the evaluation includes a prompt-injection case. This reduces the risk but does not remove it. Treat model-generated recommendations as unverified analysis; do not let posting text override application instructions or trigger privileged actions.
- The assistant **does not submit applications**, authenticate to job sites, or perform actions on behalf of an employer.

## Limitations and planned improvements

- **Scoring variance:** Local LLM output can vary between runs, changing the resulting score even when Python scoring is deterministic. The evaluation harness measures extraction variance, but not matching variance.
- **Small evaluation set:** The evaluation cases are short, illustrative examples. They show whether the pipeline behaves sensibly, not how accurate it is on real postings.
- **Unknown evidence:** An absent skill on a CV does not necessarily mean a candidate lacks it. The matcher sometimes classifies a skill with no evidence as `not_met` instead of `unknown`, which lowers both `score` and `possible_score`.
- **Priorities not enforced in code:** The matching prompt tells the model to copy priorities from the extracted requirements, but Python does not check that it did.
- **Coverage:** Keyword filtering may miss relevant jobs or include irrelevant ones; API pagination and eligibility checks need improvement.
- **Remote eligibility:** A `remote` label does not guarantee a position can be worked from Oulu or elsewhere in Finland.
- **Stale results:** Skipped jobs keep their old results. Results saved before job ids were stored are re-analyzed once. Delete `job_results.json` after changing the CV or the prompts.
- **Project suggestions:** Future versions could generate concise, targeted project plans focused on technical gaps and skip requirements that a portfolio cannot address.

## Motivation

This project explores how to combine local language models, structured outputs, deterministic business rules, and workflow orchestration to support a real-world decision process. The goal is a **transparent, practical assistant** rather than an autonomous application bot.

---

*Built for personal learning and job-search support. Keep CV content, API keys, and personal job-matching results private.*
