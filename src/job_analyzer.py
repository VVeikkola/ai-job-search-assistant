from langchain_ollama import ChatOllama
from src.models import JobAnalysis

model = ChatOllama(model="qwen3.5:9b")
structured_model = model.with_structured_output(JobAnalysis)

def analyze_job(job_description: str) -> JobAnalysis:
    return structured_model.invoke(job_description)

