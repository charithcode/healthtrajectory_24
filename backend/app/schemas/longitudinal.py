"""Pydantic contracts for longitudinal patient-report analysis and health snapshots."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.features import ExtractedFeature, ValidationResponse


class FeatureComparison(BaseModel):
    """Longitudinal comparison for a single clinical or laboratory feature."""

    canonical_name: str
    previous_value: Decimal | str | None = None
    current_value: Decimal | str | None = None
    unit: str | None = None
    absolute_change: Decimal | None = None
    percentage_change: Decimal | None = None
    direction: Literal["increased", "decreased", "unchanged", "unavailable"]
    comparison_note: str | None = None


class TrajectorySummary(BaseModel):
    """Aggregated longitudinal shifts across all tracked features."""

    total_compared: int
    increased_count: int
    decreased_count: int
    unchanged_count: int
    unavailable_count: int
    increased_features: list[str] = Field(default_factory=list)
    decreased_features: list[str] = Field(default_factory=list)
    unchanged_features: list[str] = Field(default_factory=list)
    unavailable_features: list[str] = Field(default_factory=list)
    largest_changes: list[FeatureComparison] = Field(default_factory=list)
    summary_text: str


class HealthSnapshot(BaseModel):
    """Structured current health snapshot for a single analyzed report."""

    report_id: int
    report_date: datetime | None = None
    page_count: int
    extraction_method: str
    basic_feature_count: int
    total_basic_required: int = 9
    additional_feature_count: int
    eligible_for_basic_model: bool
    missing_required_features: list[str] = Field(default_factory=list)
    core_features: list[ExtractedFeature] = Field(default_factory=list)
    additional_features: list[ExtractedFeature] = Field(default_factory=list)
    completeness_percentage: Decimal = Decimal("100.00")
    reference_interpretation_note: str = (
        "Reference interpretation unavailable: population reference ranges are not configured in this prototype."
    )


class LongitudinalAnalysisResponse(BaseModel):
    """Full API response for longitudinal report processing, comparison, and current health snapshot."""

    report_id: int
    user_id: str
    report_series_name: str
    is_baseline: bool
    message: str
    uploaded_at: datetime
    report_date: datetime | None = None
    previous_report_id: int | None = None
    previous_report_date: datetime | None = None
    page_count: int
    extraction_method: str
    validation: ValidationResponse
    extracted_features: list[ExtractedFeature]
    snapshot: HealthSnapshot | None = None
    feature_comparisons: list[FeatureComparison] = Field(default_factory=list)
    trajectory_summary: TrajectorySummary | None = None
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = (
        "Research decision-support prototype only. This longitudinal comparison is "
        "a transparent mathematical shift analysis, not a diagnosis or clinical deterioration prediction."
    )
