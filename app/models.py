"""Pydantic contracts exposed by the HTTP API."""

from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health-check response contract."""

    status: Literal["ok"]


class ErrorResponse(BaseModel):
    """Error payload returned for expected client failures."""

    detail: str


class AnalyzeResponse(BaseModel):
    """Complete audio-analysis response contract."""

    filename: str
    duration_seconds: float = Field(ge=0)
    loudness_score: float = Field(ge=0, le=100)
    loudness_classification: Literal["Too Quiet", "Good", "Too Loud"]
    leading_silence_seconds: float = Field(ge=0)
    trailing_silence_seconds: float = Field(ge=0)
    total_silence_seconds: float = Field(ge=0)
    silence_score: float = Field(ge=0, le=100)
    silence_classification: Literal["Excellent", "Good", "Fair", "Poor"]
    noise_score: float = Field(ge=0, le=100)
    noise_level_db: float
    noise_classification: Literal["Excellent", "Good", "Fair", "Poor"]
    clipping_percentage: float = Field(ge=0, le=100)
    clipping_score: float = Field(ge=0, le=100)
    clipping_classification: Literal["Excellent", "Good", "Fair", "Poor"]
    overall_quality_score: float = Field(ge=0, le=100)
    recommendation: Literal["Accept", "Review", "Re-record"]
