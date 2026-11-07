from pydantic import BaseModel, Field
from src.scoring import RequirementMatch

class JobAnalysis(BaseModel):
    company: str = Field(description="Company name")
    position: str = Field(description="Job title")
    required_skills: list[str] = Field(
        description="Required technical skills"
    )

class CVAnalysis(BaseModel):
    name: str = Field(description="Candidate's name")
    email: str | None = Field(default=None)
    phone: str | None = Field(default=None)
    skills: list[str] = Field(
        description="List of candidate's technical skills"
    )
    experience: list[str] = Field(
        description="List of candidate's previous job experiences"
    )

class MatchAnalysis(BaseModel):
    matching_skills: list[str] = Field(
        description="Job requirements supported by the CV"
    )

    missing_skills: list[str] = Field(
        description="Job requirements not supported by the CV"
    )

    recommendation: str = Field(
        description="Short recommendation about whether to apply"
    )
    score: float = Field(default=None, ge=0, le=10)
    score_reason: str
    requirements: list[RequirementMatch]