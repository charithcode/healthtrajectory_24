"""Repository for persisting and querying Users, Reports, and ReportFeatures."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.report import Report, ReportFeature, User
from app.schemas.features import ExtractedFeature


def get_or_create_user(db: Session, user_id: str) -> User:
    """Retrieve an existing user or create a new user record."""
    clean_id = user_id.strip() or "anonymous-user"
    user = db.scalar(select(User).where(User.id == clean_id))
    if user is None:
        user = User(id=clean_id)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def save_report_with_features(
    db: Session,
    user_id: str,
    report_series_name: str,
    page_count: int,
    extraction_success: bool,
    extraction_method: str,
    eligible_for_basic_model: bool,
    features: list[ExtractedFeature],
    report_date: datetime | None = None,
) -> Report:
    """Create a new report record and persist all extracted canonical features."""
    user = get_or_create_user(db, user_id)
    clean_series = report_series_name.strip() or "General Health"

    report = Report(
        user_id=user.id,
        report_series_name=clean_series,
        page_count=page_count,
        extraction_success=extraction_success,
        extraction_method=extraction_method,
        eligible_for_basic_model=eligible_for_basic_model,
        report_date=report_date,
    )
    db.add(report)
    db.flush()  # Populates report.id

    for feat in features:
        val_str = str(feat.value)
        val_numeric: Decimal | None = None
        try:
            val_numeric = Decimal(val_str)
            if not val_numeric.is_finite():
                val_numeric = None
        except (InvalidOperation, ValueError, TypeError):
            val_numeric = None

        db_feature = ReportFeature(
            report_id=report.id,
            canonical_name=feat.canonical_name,
            value_raw=val_str,
            value_numeric=val_numeric,
            unit=feat.unit,
            source=feat.source,
            source_page=feat.source_page,
            source_text=feat.source_text,
        )
        db.add(db_feature)

    db.commit()
    db.refresh(report)
    return report


def get_previous_report(
    db: Session,
    user_id: str,
    report_series_name: str,
    exclude_report_id: int | None = None,
) -> Report | None:
    """Retrieve the immediately preceding report for the specific user and report series."""
    clean_id = user_id.strip()
    clean_series = report_series_name.strip()

    query = (
        select(Report)
        .options(selectinload(Report.features))
        .where(Report.user_id == clean_id, Report.report_series_name == clean_series)
    )

    if exclude_report_id is not None:
        query = query.where(Report.id != exclude_report_id)

    query = query.order_by(Report.uploaded_at.desc(), Report.id.desc())
    return db.scalar(query)


def get_report_by_id(db: Session, report_id: int) -> Report | None:
    """Retrieve a report by ID including all associated features."""
    return db.scalar(
        select(Report).options(selectinload(Report.features)).where(Report.id == report_id)
    )
