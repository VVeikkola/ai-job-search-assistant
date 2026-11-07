from langchain_ollama import ChatOllama
from models import CVAnalysis, JobAnalysis, MatchAnalysis

model = ChatOllama(
    model="qwen3.5:9b",
    temperature=0,
    reasoning=False,
    num_predict=2048
)

with_structured_output = model.with_structured_output(
    MatchAnalysis,
    method="json_schema"
)

def analyze_match(job:JobAnalysis, cv:CVAnalysis) -> MatchAnalysis:
    """Analyze the match between a job description and a CV."""

    prompt = f"""
    You are an AI assistant that evaluates how well a candidate's
    CV matches the requirements of a job description.

    Your task is to identify matching skills, missing skills,
    and evaluate each job requirement individually.

    JOB DESCRIPTION:
    {job.model_dump_json(indent=2)}

    CANDIDATE CV:
    {cv.model_dump_json(indent=2)}

    INSTRUCTIONS:

    1. Identify the skills that are present in both the job
    description and the CV.

    2. Identify the job requirements that are not explicitly
    supported by the CV.

    3. For every distinct job requirement, create a
    RequirementMatch entry.

    4. Classify each requirement's priority:

    - required: The job description explicitly states
        that the requirement is mandatory.
    - preferred: The requirement is explicitly described
        as desirable, optional, or an advantage.

    If the priority is unclear, use "preferred" and
    explain the uncertainty in the evidence.

    5. Classify each requirement's match:

    - full: The CV provides clear evidence that the
        candidate meets the requirement.
    - partial: The CV demonstrates related or
        transferable skills.
    - not_met: The available information explicitly
        establishes that the requirement is not met.
    - unknown: The CV does not provide sufficient
        evidence to determine whether the requirement
        is met.

    6. Consider relationships between technologies.

    For example:
    - Jenkins can demonstrate CI/CD experience.
    - Docker can demonstrate containerization skills.
    - Experience with one cloud platform does not
        automatically prove experience with another.

    Evaluate these relationships based on evidence
    rather than keyword matching alone.

    7. Include evidence from the CV whenever available.
    Do not invent skills, experience, or qualifications.

    8. Evaluate each job requirement separately.
    Do not count the same requirement more than once.

    9. Do not treat missing CV information as proof
    that the candidate lacks a skill.

    10. Provide a short recommendation explaining
        whether the candidate should consider applying.

    11. Do not calculate the final suitability score.
        Python will calculate it separately.

        For compatibility with the current output schema,
        set score to 0 and score_reason to
        "Pending Python scoring".

    12. Return all fields required by the output schema,
        including:
        - matching_skills
        - missing_skills
        - requirements
        - recommendation
        - score
        - score_reason
    """

    result = with_structured_output.invoke(prompt)

    return result

if __name__ == "__main__":
    from src.job_analyzer import analyze_job
    from src.cv_analyzer import analyze_cv

    job_text = """Twoday is looking for a Software Developer.
    Required skills: Python, Azure, CI/CD.
    """

    cv_text = """
    John Smith
    Skills: Python, Docker, Jenkins.
    Experience: Software Developer at Nokia.
    """

    job = analyze_job(job_text)
    cv = analyze_cv(cv_text)

    print(f"Job text: {job_text}")
    print(f"CV text: {cv_text}")

    match = analyze_match(job, cv)

    print(match.model_dump_json(indent=2))
