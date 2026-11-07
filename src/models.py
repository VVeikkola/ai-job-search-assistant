from typing import Literal

from pydantic import BaseModel, Field

from src.scoring import RequirementMatch


class JobRequirement(BaseModel):
    name: str = Field(
        description="Short requirement name, e.g. Python or 3+ years backend"
    )

    priority: Literal["required", "preferred"] = Field(
        description="required = must have; preferred = nice to have"
    )

    category: Literal[
        "technical",
        "experience",
        "language",
        "education",
        "other"
    ] = Field(
        description="Requirement type"
    )


class JobAnalysis(BaseModel):
    company: str = Field(description="Company name")
    position: str = Field(description="Job title")
    requirements: list[JobRequirement] = Field(
        default_factory=list,
        description="Requirements stated in the job posting"
    )

class ProjectExperience(BaseModel):
    name: str = Field(
        description="Project name"
    )

    project_type: Literal[
        "university",
        "personal",
        "course_exercise"
    ] = Field(
        description="Origin of the project"
    )

    status: Literal[
        "completed",
        "in_progress"
    ] = Field(
        description="Current project status"
    )

    description: str = Field(
        description="Short description of the project"
    )

    technologies: list[str] = Field(
        description="Technologies used in the project"
    )


class SkillEvidence(BaseModel):
    skill: str = Field(
        description="Name of the technical skill"
    )

    source: str = Field(
        description=(
            "Exact employer or project name where the skill "
            "was demonstrated, such as Nokia or Mini Data Pipeline. "
            "Never use professional, project or learning as the source."
        )
    )

    evidence_type: Literal[
        "professional",
        "project",
        "learning"
    ] = Field(
        description="Experience category"
    )

class CVAnalysis(BaseModel):
    name: str = Field(
        description="Candidate name"
    )

    skills: list[str] = Field(
        description="All technical skills mentioned in the CV"
    )

    experience: list[str] = Field(
        description="Professional work experience"
    )

    education: list[str] = Field(
        default_factory=list,
        description="Education and qualifications"
    )

    projects: list[ProjectExperience] = Field(
        default_factory=list,
        description="Personal and university projects"
    )

    skill_evidence: list[SkillEvidence] = Field(
        default_factory=list,
        description="Evidence supporting technical skills"
    )
    languages: list[str] = Field(default_factory=list)

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
    score: float | None = Field(default=None, ge=0, le=10)
    score_reason: str
    requirements: list[RequirementMatch]

class JobPosting(BaseModel):
    id: str
    title: str
    company: str
    location: str
    remote: bool | None = None
    description: str
    url: str
    source: str