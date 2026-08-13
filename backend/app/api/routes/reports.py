"""Structured, PDF report validation, and longitudinal trajectory analysis endpoints."""

from decimal import Decimal
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.report_repository import (
    get_previous_report,
    save_report_with_features,
)
from app.schemas.features import (
    PdfValidationResponse,
    PredictionRequest,
    PredictionResponse,
    ValidationRequest,
    ValidationResponse,
)
from app.schemas.longitudinal import HealthSnapshot, LongitudinalAnalysisResponse
from app.services.feature_dictionary import (
    BASIC_REQUIRED_FEATURES,
    validate_basic_features,
)
from app.services.longitudinal_service import compare_features
from app.services.pdf_extractor import extract_text_from_pdf
from app.services.prediction_service import PredictionService
from app.services.report_parser import (
    parse_report_pages,
    parsed_features_to_measurements,
)

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/validate", response_model=ValidationResponse)
def validate_report(payload: ValidationRequest) -> ValidationResponse:
    return validate_basic_features(payload.measurements)


@router.post("/predict", response_model=PredictionResponse)
def predict_report(payload: PredictionRequest) -> PredictionResponse:
    return PredictionService().predict(payload.measurements)


@router.post("/pdf/validate", response_model=PdfValidationResponse)
async def validate_pdf_report(file: Annotated[UploadFile, File(...)]) -> PdfValidationResponse:
    """Extract text, parse configured features, then use the shared validation path."""

    if file.content_type not in {"application/pdf", "application/x-pdf"}:
        raise HTTPException(status_code=415, detail="Only PDF uploads are supported.")

    suffix = Path(file.filename or "report.pdf").suffix or ".pdf"
    temporary_path: Path | None = None
    try:
        with NamedTemporaryFile(delete=False, suffix=suffix) as temporary_file:
            temporary_file.write(await file.read())
            temporary_path = Path(temporary_file.name)
        extraction = extract_text_from_pdf(temporary_path)
    finally:
        await file.close()
        if temporary_path and temporary_path.exists():
            temporary_path.unlink()

    if not extraction.extraction_success:
        raise HTTPException(status_code=422, detail={"code": "invalid_pdf", "warnings": extraction.warnings})

    pages = [
        {"page_number": page.page_number, "text": page.text}
        for page in extraction.pages
    ] or [{"page_number": 1, "text": extraction.extracted_text}]

    parse_result = parse_report_pages(pages, extraction_method=extraction.extraction_method)
    validation = validate_basic_features(parsed_features_to_measurements(parse_result.features))
    return PdfValidationResponse(
        extracted_text=extraction.extracted_text,
        page_count=extraction.page_count,
        extraction_success=extraction.extraction_success,
        extraction_method=extraction.extraction_method,
        warnings=[*extraction.warnings, *parse_result.warnings],
        pages=[{"page_number": page["page_number"], "text": page["text"]} for page in pages],
        extracted_features=parse_result.features,
        validation=validation,
    )


@router.post("/pdf/predict", response_model=PredictionResponse)
async def predict_pdf_report(file: Annotated[UploadFile, File(...)]) -> PredictionResponse:
    """Extract, normalize, and predict from a PDF when the required Basic features are present."""

    if file.content_type not in {"application/pdf", "application/x-pdf"}:
        raise HTTPException(status_code=415, detail="Only PDF uploads are supported.")

    suffix = Path(file.filename or "report.pdf").suffix or ".pdf"
    temporary_path: Path | None = None
    try:
        with NamedTemporaryFile(delete=False, suffix=suffix) as temporary_file:
            temporary_file.write(await file.read())
            temporary_path = Path(temporary_file.name)
        extraction = extract_text_from_pdf(temporary_path)
    finally:
        await file.close()
        if temporary_path and temporary_path.exists():
            temporary_path.unlink()

    if not extraction.extraction_success:
        raise HTTPException(status_code=422, detail={"code": "invalid_pdf", "warnings": extraction.warnings})

    pages = [
        {"page_number": page.page_number, "text": page.text}
        for page in extraction.pages
    ] or [{"page_number": 1, "text": extraction.extracted_text}]

    parse_result = parse_report_pages(pages, extraction_method=extraction.extraction_method)
    measurements = parsed_features_to_measurements(parse_result.features)
    result = PredictionService().predict(measurements)
    result.warnings = [*extraction.warnings, *parse_result.warnings, *result.warnings]
    return result


@router.post("/pdf/analyze", response_model=LongitudinalAnalysisResponse)
async def analyze_pdf_report(
    file: Annotated[UploadFile, File(...)],
    user_id: Annotated[str, Form()] = "dev-user",
    report_series_name: Annotated[str, Form()] = "General Health",
    db: Annotated[Session, Depends(get_db)] = None,  # type: ignore[assignment]
) -> LongitudinalAnalysisResponse:
    """Ingest PDF, extract all canonical features, persist report, and evaluate longitudinal trajectory."""

    if file.content_type not in {"application/pdf", "application/x-pdf"}:
        raise HTTPException(status_code=415, detail="Only PDF uploads are supported.")

    suffix = Path(file.filename or "report.pdf").suffix or ".pdf"
    temporary_path: Path | None = None
    try:
        with NamedTemporaryFile(delete=False, suffix=suffix) as temporary_file:
            temporary_file.write(await file.read())
            temporary_path = Path(temporary_file.name)
        extraction = extract_text_from_pdf(temporary_path)
    finally:
        await file.close()
        if temporary_path and temporary_path.exists():
            temporary_path.unlink()

    if not extraction.extraction_success:
        raise HTTPException(status_code=422, detail={"code": "invalid_pdf", "warnings": extraction.warnings})

    pages = [
        {"page_number": page.page_number, "text": page.text}
        for page in extraction.pages
    ] or [{"page_number": 1, "text": extraction.extracted_text}]

    parse_result = parse_report_pages(pages, extraction_method=extraction.extraction_method)
    validation = validate_basic_features(parsed_features_to_measurements(parse_result.features))

    # Look up previous report before persisting the current one
    previous_report = get_previous_report(
        db,
        user_id=user_id,
        report_series_name=report_series_name,
    )

    # Persist the current report and all extracted features
    saved_report = save_report_with_features(
        db,
        user_id=user_id,
        report_series_name=report_series_name,
        page_count=extraction.page_count,
        extraction_success=extraction.extraction_success,
        extraction_method=extraction.extraction_method,
        eligible_for_basic_model=validation.eligible_for_basic_model,
        features=parse_result.features,
    )

    all_warnings = [*extraction.warnings, *parse_result.warnings]

    core_features = [f for f in parse_result.features if f.canonical_name in BASIC_REQUIRED_FEATURES]
    additional_features = [f for f in parse_result.features if f.canonical_name not in BASIC_REQUIRED_FEATURES]
    basic_feature_count = len({f.canonical_name for f in core_features})
    completeness_pct = (
        Decimal(basic_feature_count) / Decimal(len(BASIC_REQUIRED_FEATURES)) * Decimal(100)
    ).quantize(Decimal("0.01"))

    snapshot = HealthSnapshot(
        report_id=saved_report.id,
        report_date=saved_report.report_date,
        page_count=saved_report.page_count,
        extraction_method=saved_report.extraction_method,
        basic_feature_count=basic_feature_count,
        total_basic_required=len(BASIC_REQUIRED_FEATURES),
        additional_feature_count=len(additional_features),
        eligible_for_basic_model=validation.eligible_for_basic_model,
        missing_required_features=validation.missing_required_features,
        core_features=core_features,
        additional_features=additional_features,
        completeness_percentage=completeness_pct,
    )

    if previous_report is None:
        return LongitudinalAnalysisResponse(
            report_id=saved_report.id,
            user_id=saved_report.user_id,
            report_series_name=saved_report.report_series_name,
            is_baseline=True,
            message="Baseline established. Future reports in this series can be compared against this report.",
            uploaded_at=saved_report.uploaded_at,
            report_date=saved_report.report_date,
            previous_report_id=None,
            previous_report_date=None,
            page_count=saved_report.page_count,
            extraction_method=saved_report.extraction_method,
            validation=validation,
            extracted_features=parse_result.features,
            snapshot=snapshot,
            feature_comparisons=[],
            trajectory_summary=None,
            warnings=all_warnings,
        )

    # Subsequent report in the same series: compare against immediately previous report
    comparisons, trajectory = compare_features(
        previous_items=previous_report.features,
        current_items=parse_result.features,
    )

    prev_dt = previous_report.report_date or previous_report.uploaded_at

    return LongitudinalAnalysisResponse(
        report_id=saved_report.id,
        user_id=saved_report.user_id,
        report_series_name=saved_report.report_series_name,
        is_baseline=False,
        message="Longitudinal trajectory analysis generated against previous report.",
        uploaded_at=saved_report.uploaded_at,
        report_date=saved_report.report_date,
        previous_report_id=previous_report.id,
        previous_report_date=prev_dt,
        page_count=saved_report.page_count,
        extraction_method=saved_report.extraction_method,
        validation=validation,
        extracted_features=parse_result.features,
        snapshot=snapshot,
        feature_comparisons=comparisons,
        trajectory_summary=trajectory,
        warnings=all_warnings,
    )
