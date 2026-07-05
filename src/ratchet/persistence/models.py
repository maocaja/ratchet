"""Modelos SQLAlchemy 2.0 (aislados tras el puerto; el core NO los importa directo)."""

from __future__ import annotations

from typing import Any

from sqlalchemy import String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class RunRow(Base):
    """Un `RunRecord` serializado, idempotente por `state_key` (UNIQUE — §P-1/BR-73)."""

    __tablename__ = "runs"
    __table_args__ = (UniqueConstraint("state_key", name="uq_runs_state_key"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    state_key: Mapped[str] = mapped_column(Text, nullable=False)  # UNIQUE (via __table_args__)
    run_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)


class GoldenSetRow(Base):
    """Golden set versionado e inmutable (BR-21); la versión es la identidad."""

    __tablename__ = "golden_sets"

    version: Mapped[str] = mapped_column(String, primary_key=True)
    gs_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)


class BaselineRow(Base):
    """Baseline versionado e inmutable (BR-21)."""

    __tablename__ = "baselines"

    version: Mapped[str] = mapped_column(String, primary_key=True)
    baseline_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
