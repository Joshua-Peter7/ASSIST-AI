"""Database models for persisted compliance reports."""

from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""


class ComplianceReportRecord(Base):
    """Stores completed compliance reports as JSON strings."""

    __tablename__ = "compliance_reports"

    session_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    customer_id: Mapped[str] = mapped_column(String(128), nullable=False)
    agent_id: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="ready", nullable=False)
    report_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
