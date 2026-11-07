from langchain_ollama import ChatOllama
from src.models import CVAnalysis


model = ChatOllama(
    model="qwen3.5:9b",
    temperature=0
)

structured_model = model.with_structured_output(CVAnalysis)


def analyze_cv(cv_text: str) -> CVAnalysis:
    """Extract candidate information from CV text."""

    prompt = f"""
    Analyze the following CV.

    Extract the candidate's name, technical skills
    and work experience.

    Only include information explicitly supported by the CV.
    Do not invent skills or experience.

    CV:
    {cv_text}
    """

    result = structured_model.invoke(prompt)

    return result


if __name__ == "__main__":

    example_cv = """
    John Smith
    Software Developer

    Skills: Python, Docker, Git, Jenkins, SQL

    Experience:
    - Software Developer at Nokia
    - Developed Python test automation
    - Maintained Jenkins CI pipelines
    """

    result = analyze_cv(example_cv)

    print(result.model_dump_json(indent=2))