"""Pydantic contracts for structured health measurements.

These schemas deliberately validate data shape and feature availability only. They do
not make clinical judgments or apply medical alert thresholds.
"""

from decimal import Decimal, InvalidOperation
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class FeatureMeasurement(BaseModel):
    """A single user-entered or extracted measurement."""

    name: str = Field(min_length=1, max_length=100)
    value: Decimal | str
    unit: str | None = Field(default=None, max_length=32)
    source: Literal["structured", "pdf_text", "ocr", "derived"] = "structured"
    source_page: int | None = None
    source_text: str | None = None

    @field_validator("value", mode="before")
    @classmethod
    def coerce_numeric_strings(cls, value: Decimal | str) -> Decimal | str:
        if not isinstance(value, str):
            return value

        stripped = value.strip()
        if not stripped:
            return value

        try:
            decimal_value = Decimal(stripped)
        except InvalidOperation:
            return value

        if not decimal_value.is_finite():
            raise ValueError("Value must be finite.")
        return decimal_value

    @field_validator("value")
    @classmethod
    def ensure_value_is_finite(cls, value: Decimal | str) -> Decimal | str:
        if isinstance(value, Decimal) and not value.is_finite():
            raise ValueError("Value must be finite.")
        return value

    @field_validator("name")
    @classmethod
    def normalise_name(cls, value: str) -> str:
        return " ".join(value.lower().strip().split())

    @field_validator("unit")
    @classmethod
    def normalise_unit(cls, value: str | None) -> str | None:
        return value.strip() if value else None


class ValidationRequest(BaseModel):
    """Measurements submitted for Basic-tier eligibility assessment."""

    measurements: list[FeatureMeasurement] = Field(min_length=1, max_length=100)


class InvalidFeature(BaseModel):
    name: str
    canonical_name: str | None = None
    reason: str
    source_page: int | None = None
    source_text: str | None = None


class NormalizedFeature(BaseModel):
    canonical_name: str
    value: Decimal | str
    unit: str | None
    source: str


class ValidationResponse(BaseModel):
    eligible_for_basic_model: bool
    required_features: list[str]
    available_features: list[str]
    missing_required_features: list[str]
    invalid_features: list[InvalidFeature]
    normalized_features: list[NormalizedFeature]
    derived_features: list[str]
    message: str
    disclaimer: str


class PredictionRequest(BaseModel):
    measurements: list[FeatureMeasurement] = Field(min_length=1, max_length=100)


class InfluentialFeature(BaseModel):
    feature: str
    importance: float = Field(ge=0.0, le=1.0)
    direction: Literal["increases_risk", "decreases_risk", "uncertain"]


class PredictionResponse(BaseModel):
    prediction_available: bool
    prediction_status: Literal["demo", "model", "unavailable"]
    risk_probability: float | None = Field(default=None, ge=0.0, le=1.0)
    risk_level: Literal["LOW", "MODERATE", "HIGH"] | None = None
    model_version: str | None = None
    features_used: list[str] = Field(default_factory=list)
    influential_features: list[InfluentialFeature] = Field(default_factory=list)
    missing_required_features: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str


class ExtractedFeature(FeatureMeasurement):
    """A measurement parsed from a PDF or an OCR result with source traceability."""

    canonical_name: str
    source_text: str
    source_page: int
    extraction_method: Literal["pdf_text", "ocr"]
    confidence: Decimal | None = None


class PageText(BaseModel):
    page_number: int
    text: str


class PdfExtractionResponse(BaseModel):
    extracted_text: str
    page_count: int
    extraction_success: bool
    extraction_method: Literal["pdf_text", "ocr", "none"]
    warnings: list[str]
    pages: list[PageText] = Field(default_factory=list)


class PdfValidationResponse(PdfExtractionResponse):
    extracted_features: list[ExtractedFeature]
    validation: ValidationResponse
