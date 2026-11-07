from langchain_ollama import ChatOllama

from src.models import CVAnalysis, JobAnalysis, MatchAnalysis

model = ChatOllama(
    model="qwen3.5:9b",
    temperature=0,
    reasoning=False,
    num_predict=4096
)

with_structured_output = model.with_structured_output(
    MatchAnalysis,
    method="json_schema"
)

def analyze_match(job:JobAnalysis, cv:CVAnalysis) -> MatchAnalysis:
    """Analyze the match between a job description and a CV."""

    prompt = f"""
    You evaluate how well a candidate's CV matches a job.

    JOB:
    {job.model_dump_json(indent=2)}

    CV:
    {cv.model_dump_json(indent=2)}

    TASK:
    The JOB contains a list of extracted requirements. Each one already
    has a name, priority ("required" or "preferred") and category.

    Evaluate every requirement in JOB.requirements exactly once.

    For each requirement, return a RequirementMatch entry:
    - name: copy the requirement name from JOB.requirements
    - priority: copy the priority from JOB.requirements unchanged
    - match: "full", "partial", "not_met", or "unknown"
    - evidence: concrete supporting evidence or explanation

    Do not change priorities, add requirements, or drop requirements.

    MATCH CLASSIFICATION:
    - full: CV clearly demonstrates the exact required capability
    - partial: relevant transferable skills, but not full evidence
    - not_met: CV explicitly proves the requirement is not met
    - unknown: insufficient evidence

    EVIDENCE RULES:
    - Professional experience is stronger evidence than projects.
    - Personal projects can demonstrate technical competence.
    - Related technologies may justify partial matches.
    - Do not equate personal projects with production experience.
    - Consider explicit seniority and experience requirements.
    - Do not infer language proficiency from location or education.
    - Never invent qualifications.
    - Do not treat missing CV information as proof of lacking a skill.
    - Do not duplicate requirements.

    IMPORTANT:
    Return a complete requirements list.
    Every requirement must have a priority, match, and evidence.
    This list is essential for Python scoring.

    Also return:
    - matching_skills: supported relevant skills
    - missing_skills: requirements not fully demonstrated
    - recommendation: short realistic evaluation
    - score: 0
    - score_reason: "Pending Python scoring"

    Return all fields required by the schema.
    """

    result = with_structured_output.invoke(prompt)

    return result

if __name__ == "__main__":
    from src.cv_analyzer import analyze_cv
    from src.job_analyzer import analyze_job

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
