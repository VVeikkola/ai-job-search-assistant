import os

import httpx
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("HEADCOUNTLABS_API_KEY")

if not api_key:
    raise ValueError("API key not found!")

response = httpx.get(
    "https://api.headcountlabs.com/v1/jobs",
    headers={
        "Authorization": f"Bearer {api_key}"
    },
    params={
        "country": "FI",
        "city": "Oulu",
        "limit": 5
    },
    timeout=30
)

print("HTTP STATUS:", response.status_code)

response.raise_for_status()

data = response.json()

print("Jobs returned:", len(data.get("data", [])))

jobs = data.get("data", [])

if jobs:
    first_job = jobs[0]

    print("\nFIRST JOB:")
    print("Available fields:", list(first_job.keys()))

    print("\nEXAMPLE VALUES:")

    for key in [
        "job_id",
        "title",
        "employer_name",
        "locations",
        "work_arrangement",
        "description",
        "postings"
    ]:
        value = first_job.get(key)
        print(f"{key}: {str(value)[:200]}")