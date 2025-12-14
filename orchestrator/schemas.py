from pydantic import BaseModel, Field
from typing import List

class RiskReport(BaseModel):
    report_text: str = Field(
        ..., 
        description=(
            "Comprehensive financial risk assessment report in Turkish (minimum 1000 words). "
            "MUST include: Executive Summary, Company Info, Banned List Analysis, Detailed News Analysis, "
            "Risk Assessment (financial/legal/reputational/operational), and Conclusions with recommendations. "
            "Use professional language with specific data points, examples, and detailed findings. "
            "Plain text format, no markdown symbols."
        )
    )
    is_banned: bool = Field(..., description="True if the company is found in the Banned List, False otherwise.")
    confidence_score: int = Field(..., description="Confidence score between 0 and 100 based on data quality and findings.")
    sources: List[str] = Field(
        ..., 
        description=(
            "List of ALL data sources with URLs where applicable. "
            "Format: ['Resmi Gazete', 'https://news.google.com/...', 'https://hurriyet.com.tr/...', etc.]. "
            "Include EVERY news article link mentioned in the report."
        )
    )
    status: str = Field(..., description="Report generation status: 'SUCCESS' or 'ERROR'.")
