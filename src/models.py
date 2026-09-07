from pydantic import BaseModel, Field
from typing import List

class ScoreBreakdown(BaseModel):
    ai_project_depth: int = Field(description="Score out of 40. Penalize thin API wrappers.")
    python_backend: int = Field(description="Score out of 30. Reward practical implementations.")
    cloud_fullstack: int = Field(description="Score out of 15.")
    engineering_depth: int = Field(description="Score out of 5.")
    # GitHub is scored separately out of 10

class ResumeEvaluation(BaseModel):
    candidate_name: str = Field(default="Unknown")
    matched_skills: List[str] = Field(default_factory=list)
    project_summary: str = Field(default="No summary provided.")
    strengths: List[str] = Field(default_factory=list)
    concerns: List[str] = Field(default_factory=list)
    score_breakdown: ScoreBreakdown
