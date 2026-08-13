"""SQLAlchemy ORM models for Users, Reports, and Extracted Features."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(128), primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    reports: Mapped[list[Report]] = relationship("Report", back_populates="user", cascade="all, delete-orphan")


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(128), ForeignKey("users.id"), index=True, nullable=False)
    report_series_name: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    report_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    page_count: Mapped[int] = mapped_column(Integer, default=1)
    extraction_success: Mapped[bool] = mapped_column(Boolean, default=True)
    extraction_method: Mapped[str] = mapped_column(String(32), default="ocr")
    eligible_for_basic_model: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped[User] = relationship("User", back_populates="reports")
    features: Mapped[list[ReportFeature]] = relationship("ReportFeature", back_populates="report", cascade="all, delete-orphan", order_by="ReportFeature.id")

    __table_args__ = (
        Index("ix_reports_user_series", "user_id", "report_series_name"),
        Index("ix_reports_user_series_uploaded", "user_id", "report_series_name", "uploaded_at"),
    )


class ReportFeature(Base):
    __tablename__ = "report_features"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_id: Mapped[int] = mapped_column(Integer, ForeignKey("reports.id"), index=True, nullable=False)
    canonical_name: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    value_raw: Mapped[str] = mapped_column(String(128), nullable=False)
    value_numeric: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    source: Mapped[str] = mapped_column(String(32), default="ocr")
    source_page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    report: Mapped[Report] = relationship("Report", back_populates="features")

    __table_args__ = (
        Index("ix_report_features_report_canonical", "report_id", "canonical_name"),
    )
