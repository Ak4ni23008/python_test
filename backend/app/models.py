"""Database models for strategies, deployments, backtests, and live execution."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120), default="Trader")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    strategies: Mapped[list["Strategy"]] = relationship(back_populates="user")


class Strategy(Base):
    __tablename__ = "strategies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    english_prompt: Mapped[str] = mapped_column(Text)
    config_json: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(32), default="draft")  # draft | active | archived
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="strategies")
    deployments: Mapped[list["Deployment"]] = relationship(back_populates="strategy")
    backtest_reports: Mapped[list["BacktestReport"]] = relationship(back_populates="strategy")


class Deployment(Base):
    __tablename__ = "deployments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    strategy_id: Mapped[str] = mapped_column(String(36), ForeignKey("strategies.id"), index=True)
    mode: Mapped[str] = mapped_column(String(16), default="simulation")  # simulation | live
    status: Mapped[str] = mapped_column(String(32), default="pending")  # pending | running | stopped | error
    host: Mapped[str] = mapped_column(String(120), default="railway-worker")
    running_pnl: Mapped[float] = mapped_column(Float, default=0.0)
    open_position: Mapped[bool] = mapped_column(Boolean, default=False)
    position_qty: Mapped[int] = mapped_column(Integer, default=0)
    entry_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_price: Mapped[float] = mapped_column(Float, default=0.0)
    tick_count: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    stopped_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    strategy: Mapped["Strategy"] = relationship(back_populates="deployments")
    execution_logs: Mapped[list["ExecutionLog"]] = relationship(back_populates="deployment")
    live_trades: Mapped[list["LiveTrade"]] = relationship(back_populates="deployment")


class BacktestReport(Base):
    __tablename__ = "backtest_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    strategy_id: Mapped[str] = mapped_column(String(36), ForeignKey("strategies.id"), index=True)
    metrics: Mapped[dict] = mapped_column(JSON)
    equity_curve: Mapped[list] = mapped_column(JSON)
    drawdown_curve: Mapped[list] = mapped_column(JSON)
    trades: Mapped[list] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    strategy: Mapped["Strategy"] = relationship(back_populates="backtest_reports")


class ExecutionLog(Base):
    __tablename__ = "execution_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    deployment_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("deployments.id"), nullable=True, index=True)
    strategy_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("strategies.id"), nullable=True, index=True)
    level: Mapped[str] = mapped_column(String(16), default="info")
    message: Mapped[str] = mapped_column(Text)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    deployment: Mapped["Deployment | None"] = relationship(back_populates="execution_logs")


class LiveTrade(Base):
    __tablename__ = "live_trades"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    deployment_id: Mapped[str] = mapped_column(String(36), ForeignKey("deployments.id"), index=True)
    side: Mapped[str] = mapped_column(String(8))  # buy | sell
    price: Mapped[float] = mapped_column(Float)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    pnl: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    deployment: Mapped["Deployment"] = relationship(back_populates="live_trades")
