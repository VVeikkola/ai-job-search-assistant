import json
from pathlib import Path

from langchain_ollama import ChatOllama
from src.models import CVAnalysis


model = ChatOllama(
    model="qwen3.5:9b",
    temperature=0,
    reasoning=False,
    num_predict=8192
)

structured_model = model.with_structured_output(
    CVAnalysis,
    method="json_schema"
)


def analyze_cv(cv_text: str) -> CVAnalysis:
    """Extract candidate information from CV text."""

    prompt = f"""
    You are an AI assistant that extracts structured information
    from a candidate's CV.

    Return a complete CVAnalysis object matching the required schema.

    CANDIDATE PROFILE:

    {cv_text}

    EXTRACTION RULES:

    1. NAME
    - Extract the candidate's name if explicitly provided.
    - Otherwise use "Not specified".

    2. SKILLS
    - Extract technical skills explicitly supported by the CV.
    - Avoid duplicates.
    - Keep skill names concise.

    3. EXPERIENCE
    - Extract professional employment experience.
    - Include employer, role and relevant responsibilities.
    - Keep each experience description concise.
    - Do not classify university or personal projects as employment.

    4. EDUCATION
    - Extract degrees, institutions and graduation status.
    - Do not invent qualifications.

    5. PROJECTS
    Extract personal, university and coursework projects.

    For each project, include:
    - name
    - project_type
    - status
    - description
    - technologies

    PROJECT TYPES:
    - university: University development or team projects.
    - personal: Independently developed projects.
    - course_exercise: Coursework and learning exercises.

    PROJECT STATUS:
    - completed: Finished project or working MVP.
    - in_progress: Ongoing or unfinished project.

    If status is unclear, use "in_progress".

    Keep descriptions short, preferably 1-2 sentences.

    6. SKILL EVIDENCE

    Return at most 20 skill_evidence entries.

    Prioritize:
    - Professional experience
    - Important technical skills
    - Relevant project experience

    Each entry must contain:
    - skill
    - source
    - evidence_type

    EVIDENCE TYPES:
    - professional: Skills used in actual employment.
    - project: Skills demonstrated in personal or university projects.
    - learning: Skills practiced in coursework or learning exercises.

    The source must be the actual employer or project name.

    Examples:
    - Python | Nokia | professional
    - LangGraph | Local AI Job Search Assistant | project
    - PyTorch | AI Infrastructure Learning | learning

    Do not duplicate evidence entries.
    Do not return empty objects in skill_evidence.

    7. LANGUAGES

    Extract all languages explicitly documented in the CV.

    Preserve the proficiency levels exactly as written.

    Examples:
    - "Finnish: Native"
    - "English: Professional working proficiency"

    Do not infer language skills from nationality,
    education, location or candidate name.

    If no languages are documented, return an empty list.

    IMPORTANT RULES:

    - Only use information supported by the CV.
    - Never invent skills, qualifications or experience.
    - Do not confuse project experience with professional employment.
    - Do not mark ongoing projects as completed without evidence.
    - Keep descriptions concise.
    - Avoid unnecessary repetition.
    - Return valid structured data matching CVAnalysis.

    REQUIRED OUTPUT FIELDS:

    - name
    - skills
    - experience
    - education
    - projects
    - skill_evidence
    - languages

    Every skill_evidence entry must contain all required fields.
    Always return the languages field.
    """

    result = structured_model.invoke(prompt)

    cache_path = Path("data/private/cv_analysis.json")
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    cache_path.write_text(
        result.model_dump_json(indent=2),
        encoding="utf-8"
    )

    return result


if __name__ == "__main__":

    from pathlib import Path

    cv_path = Path("data/private/cv.txt")
    cv_text = cv_path.read_text(encoding="utf-8")

    result = analyze_cv(cv_text)

    print("\nTECHNICAL SKILLS:")
    print(result.skills)

    print("\nPROJECTS:")
    for project in result.projects:
        print(
            f"{project.name} | "
            f"{project.project_type} | "
            f"{project.status}"
        )

    print("\nSKILL EVIDENCE:")
    for evidence in result.skill_evidence:
        print(
            f"{evidence.skill} | "
            f"{evidence.source} | "
            f"{evidence.evidence_type}"
        )

    print("\nLANGUAGES:")
    for language in result.languages:
        print("-", language)