import os

import httpx
from dotenv import load_dotenv

from src.models import JobPosting


load_dotenv()

BASE_URL = "https://api.headcountlabs.com/v1/jobs"


def get_value(field):
    """Extract value from an API field."""

    if not isinstance(field, dict):
        return None

    if field.get("state") != "known":
        return None

    return field.get("value")


def fetch_jobs(params: dict) -> list[dict]:
    """Fetch jobs from Headcount Labs."""

    api_key = os.getenv("HEADCOUNTLABS_API_KEY")

    if not api_key:
        raise ValueError("API key missing")

    response = httpx.get(
        BASE_URL,
        headers={
            "Authorization": f"Bearer {api_key}"
        },
        params=params,
        timeout=30
    )

    response.raise_for_status()

    return response.json().get("data", [])


def normalize_job(job: dict) -> JobPosting | None:
    """Convert API response into JobPosting."""

    title = get_value(job.get("title"))
    company = get_value(job.get("employer_name"))
    description = get_value(job.get("description"))

    if not title or not description:
        return None

    locations = []

    for location in job.get("locations", []):
        value = get_value(location)

        if value:
            city = value.get("city")
            country = value.get("country")

            if city:
                locations.append(city)
            elif country:
                locations.append(country)

    arrangement = get_value(job.get("work_arrangement"))

    remote = None

    if arrangement == "remote":
        remote = True
    elif arrangement in ("hybrid", "in_person"):
        remote = False

    url = ""

    for posting in job.get("postings", []):
        if posting.get("posting_status") != "listed":
            continue

        url = (
            get_value(posting.get("application_url"))
            or get_value(posting.get("posting_url"))
            or ""
        )

        if url:
            break

    return JobPosting(
        id=str(job["job_id"]),
        title=title,
        company=company or "Unknown",
        location=", ".join(dict.fromkeys(locations)) or "Unknown",
        remote=remote,
        description=description,
        url=url,
        source="Headcount Labs"
    )


KEYWORDS = (
    "software developer",
    "software engineer",
    "python developer",
    "backend developer",
    "full stack",
    "full-stack",
    "frontend developer",
    "ai engineer",
    "ai developer",
    "machine learning engineer",
    "data engineer",
    "mlops",
    "devops engineer",
    "test automation",
    "qa engineer",
    "quality assurance engineer",
    "automation engineer",
    "platform engineer",
    "site reliability engineer",
    "embedded software",
    "firmware engineer",
    "ohjelmistokehittäjä",
    "ohjelmistosuunnittelija",
    "sovelluskehittäjä",
)


def search_jobs() -> list[JobPosting]:
    """Search jobs in Oulu and remote jobs in Finland."""

    searches = [
        {
            "country": "FI",
            "city": "Oulu",
            "currentness": "current",
            "limit": 100
        },
        {
            "country": "FI",
            "work_arrangement": "remote",
            "currentness": "current",
            "limit": 100
        }
    ]

    found_jobs = {}

    for params in searches:
        raw_jobs = fetch_jobs(params)

        for raw_job in raw_jobs:
            job = normalize_job(raw_job)

            if job is None:
                continue

            if not any(
                keyword in job.title.lower()
                for keyword in KEYWORDS
            ):
                continue

            found_jobs[job.id] = job

    return list(found_jobs.values())


if __name__ == "__main__":

    jobs = search_jobs()

    print(f"\nFound {len(jobs)} relevant jobs\n")

    for job in jobs:
        print(f"{job.title} — {job.company}")
        print(f"Location: {job.location}")
        print(f"Remote: {job.remote}")
        print(f"URL: {job.url}")
        print("-" * 50)