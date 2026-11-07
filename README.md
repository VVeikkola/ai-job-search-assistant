# AI Job Search Assistant

A local, privacy-conscious job-search assistant built with **Python, LangGraph, Ollama, and Qwen**. It fetches job postings through the Headcount Labs API, compares their requirements with a structured CV profile, assigns an explainable suitability score, and suggests areas for portfolio development.

> **Project status:** Working local prototype. Scores are advisory, not predictions of hiring decisions.

## Features

- **Automated job discovery:** Searches for software, AI, data, and automation roles in Oulu and remote roles listed for Finland using Headcount Labs.
- **Structured CV analysis:** Uses a local LLM to extract skills, professional experience, education, projects, evidence of skills, and language proficiency.
- **CV analysis cache:** Saves the structured CV to a private local JSON file, avoiding repeated CV extraction on every search.
- **Job-to-CV matching:** Evaluates job requirements with evidence-based categories (`full`, `partial`, `not_met`, `unknown`) and priorities (`required`, `preferred`).
- **Deterministic scoring:** Python calculates a score from 0 to 10. Required requirements carry weight **3**, preferred requirements weight **1**; full matches earn full weight and partial matches half weight.
- **LangGraph workflow:** Runs job analysis, matching, scoring, and conditional routing.
- **Project suggestions:** For scores of **5/10 or higher**, the workflow produces a basic suggestion based on skills that are not fully demonstrated, when applicable.
- **Local results:** Saves the analyzed job list to JSON, including scores, recommendations, suggestions, and application URLs.

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

> **Batch size:** The number of jobs processed depends on the current loop in `src/job_search.py` (`jobs[:3]` for a three-job test or `jobs` for the full fetched list). The API fetcher itself currently retrieves a limited number of results per search; full pagination has not yet been implemented.

### Run the tests

```bash
uv run python -m pytest tests/test_scoring.py -v
```

### Run the extraction evaluation

Requires Ollama running locally, so it is not part of CI:

```bash
uv run python -m evals.run_eval
```

## How matching and scoring work

The job evaluator assigns each extracted requirement:

- **Priority:** `required` (weight 3) or `preferred` (weight 1).
- **Match:** `full` (100% credit), `partial` (50%), `not_met` (0%), or `unknown` (0% in the current score).

The weighted score is scaled to **0–10**. A requirement without evidence is classified as `unknown`, rather than being treated as proof that the candidate lacks the skill. However, unknowns currently contribute no points, so the numeric score can still underestimate a candidate whose CV omits relevant information.

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
├── src/
│   ├── models.py           # Pydantic CV, job, and match models
│   ├── cv_analyzer.py      # Local CV extraction and caching
│   ├── job_fetcher.py      # Headcount Labs API and job filtering
│   ├── job_analyzer.py     # Job requirement extraction
│   ├── match_analyzer.py   # Evidence-based requirement matching
│   ├── scoring.py          # Deterministic weighted scoring
│   ├── graph.py            # LangGraph matching workflow
│   └── job_search.py       # Search entry point and result storage
├── tests/
│   └── test_scoring.py
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
- Job postings and their descriptions are external, untrusted content. Treat model-generated recommendations as unverified analysis; do not let posting text override application instructions or trigger privileged actions.
- The assistant **does not submit applications**, authenticate to job sites, or perform actions on behalf of an employer.

## Limitations and planned improvements

- **Scoring variance:** Local LLM requirement extraction can vary between runs, changing the resulting score even when Python scoring is deterministic.
- **Incomplete requirements:** Some job-analysis fields currently emphasize technical skills; years of experience, seniority, and language constraints may require more structured extraction.
- **Unknown evidence:** An absent skill on a CV does not necessarily mean a candidate lacks it.
- **Coverage:** Keyword filtering may miss relevant jobs or include irrelevant ones; API pagination and eligibility checks need improvement.
- **Remote eligibility:** A `remote` label does not guarantee a position can be worked from Oulu or elsewhere in Finland.
- **Resuming runs:** JSON results are saved during processing, but rerunning the script can still re-analyze previously processed jobs.
- **Project suggestions:** Future versions could generate concise, targeted project plans focused on technical gaps and skip requirements that a portfolio cannot address.

## Motivation

This project explores how to combine local language models, structured outputs, deterministic business rules, and workflow orchestration to support a real-world decision process. The goal is a **transparent, practical assistant** rather than an autonomous application bot.

---

*Built for personal learning and job-search support. Keep CV content, API keys, and personal job-matching results private.*
