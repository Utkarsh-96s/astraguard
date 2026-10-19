"""SQLAlchemy 2 database models for ASTRA-GUARD core tables."""
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy entities."""
    pass


class Asset(Base):
    """Spacecraft asset monitored by the platform."""
    __tablename__ = "assets"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    norad_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    type: Mapped[str] = mapped_column(String(64), default="satellite")
    tle_epoch: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    telemetry = relationship("Telemetry", back_populates="asset")
    risk_snapshots = relationship("RiskSnapshot", back_populates="asset")


class Telemetry(Base):
    """Time-series telemetry points."""
    __tablename__ = "telemetry"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    asset_id: Mapped[str] = mapped_column(String(64), ForeignKey("assets.id"), nullable=False, index=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    quality: Mapped[float] = mapped_column(Float, default=1.0)
    synthetic: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    asset = relationship("Asset", back_populates="telemetry")

    __table_args__ = (
        Index("ix_telemetry_asset_ts", "asset_id", "ts"),
    )


class TelemetryWindow(Base):
    """Processed window of telemetry with health evaluation."""
    __tablename__ = "telemetry_windows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    asset_id: Mapped[str] = mapped_column(String(64), ForeignKey("assets.id"), nullable=False, index=True)
    t_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    t_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    model_ver: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class SpaceObject(Base):
    """Catalog of space objects (active satellites, space debris, rocket bodies)."""
    __tablename__ = "objects"

    norad_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    type: Mapped[str] = mapped_column(String(32), default="debris")  # debris / payload / r/b
    tle_line1: Mapped[str] = mapped_column(String(80), nullable=False)
    tle_line2: Mapped[str] = mapped_column(String(80), nullable=False)
    epoch: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Conjunction(Base):
    """Conjunction assessment event between a primary asset and a secondary object."""
    __tablename__ = "conjunctions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    primary_id: Mapped[str] = mapped_column(String(64), ForeignKey("assets.id"), nullable=False)
    secondary_id: Mapped[int] = mapped_column(Integer, ForeignKey("objects.norad_id"), nullable=False)
    tca: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    miss_km: Mapped[float] = mapped_column(Float, nullable=False)
    rel_vel_kms: Mapped[float] = mapped_column(Float, nullable=False)
    pc: Mapped[float] = mapped_column(Float, nullable=False)
    pc_method: Mapped[str] = mapped_column(String(32), default="foster_2d_screening")
    risk_class: Mapped[str] = mapped_column(String(32), default="LOW")
    synthetic: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class ImageryProduct(Base):
    """Earth Observation satellite imagery product."""
    __tablename__ = "imagery_products"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source: Mapped[str] = mapped_column(String(64), default="Sentinel-2")
    bbox: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    acquired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    cloud_pct: Mapped[float] = mapped_column(Float, default=0.0)
    uri: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class DisasterEvent(Base):
    """Disaster event identified and prioritized by the Disaster AI module."""
    __tablename__ = "disaster_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    product_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("imagery_products.id"), nullable=True)
    type: Mapped[str] = mapped_column(String(64), nullable=False)  # flood / wildfire / damage
    area_km2: Mapped[float] = mapped_column(Float, default=0.0)
    mask_uri: Mapped[str | None] = mapped_column(String(512), nullable=True)
    priority: Mapped[float] = mapped_column(Float, default=0.0)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    synthetic: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class RiskSnapshot(Base):
    """Fused mission risk score snapshot for an asset at a point in time."""
    __tablename__ = "risk_snapshots"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    asset_id: Mapped[str] = mapped_column(String(64), ForeignKey("assets.id"), nullable=False, index=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    r_h: Mapped[float] = mapped_column(Float, nullable=False)  # Spacecraft Health risk (0..1)
    r_d: Mapped[float] = mapped_column(Float, nullable=False)  # Debris Collision risk (0..1)
    r_e: Mapped[float] = mapped_column(Float, nullable=False)  # EO Disaster priority (0..1)
    score: Mapped[float] = mapped_column(Float, nullable=False)  # Fused Mission Risk Score (0..100)
    level: Mapped[str] = mapped_column(String(32), nullable=False)  # NOMINAL / WATCH / WARNING / CRITICAL
    drivers: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    synthetic: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    asset = relationship("Asset", back_populates="risk_snapshots")
    alerts = relationship("Alert", back_populates="snapshot")


class Alert(Base):
    """Mission alert generated when risk crosses threshold."""
    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    snapshot_id: Mapped[str] = mapped_column(String(64), ForeignKey("risk_snapshots.id"), nullable=False)
    level: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE")  # ACTIVE / ACKNOWLEDGED / DISMISSED
    dedup_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    synthetic: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    snapshot = relationship("RiskSnapshot", back_populates="alerts")
    actions = relationship("OperatorAction", back_populates="alert")


class OperatorAction(Base):
    """Human-in-the-loop action record (audit log)."""
    __tablename__ = "operator_actions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    alert_id: Mapped[str] = mapped_column(String(64), ForeignKey("alerts.id"), nullable=False)
    user: Mapped[str] = mapped_column(String(128), default="Operator")
    action: Mapped[str] = mapped_column(String(32), nullable=False)  # approve / dismiss / snooze
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    alert = relationship("Alert", back_populates="actions")


class ModelRegistry(Base):
    """Metadata registry of trained and loaded models."""
    __tablename__ = "model_registry"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    metrics: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    trained_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    data_hash: Mapped[str] = mapped_column(String(128), nullable=False)
