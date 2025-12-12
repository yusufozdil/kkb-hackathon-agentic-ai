from pydantic import BaseModel, Field
from typing import List

class RiskReport(BaseModel):
    report_text: str = Field(..., description="A detailed financial risk assessment report in Turkish markdown format.")
    is_banned: bool = Field(..., description="True if the company is found in the Banned List, False otherwise.")
    confidence_score: int = Field(..., description="Confidence score between 0 and 100.")
    sources: List[str] = Field(..., description="List of sources cited in the report.")
    status: str = Field(..., description="Status of the report, e.g., 'SUCCESS'.")
