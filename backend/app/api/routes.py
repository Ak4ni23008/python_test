"""REST API for CloudTrade platform."""

from __future__ import annotations

import socket
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.ai.gemini_strategy import english_to_strategy_config
from app.ai.code_generator import english_to_python_code
from app.config import get_settings
from app.database import get_db
from app.engines.backtest_engine import run_backtest
from app.engines.live_engine import clear_state
from app.engines.strategy_schema import StrategyConfig
from app.models import BacktestReport, Deployment, ExecutionLog, LiveTrade, Strategy
from app.services.bootstrap import ensure_demo_user
from app.services.code_executor import execute_strategy_code

router = APIRouter(prefix="/api")
settings = get_settings()
HOST = socket.gethostname()


class ParseStrategyRequest(BaseModel):
    english: str = Field(..., min_length=5, max_length=4000)
    name: str = Field(default="My Strategy", max_length=200)


class StrategyUpdateRequest(BaseModel):
    name: str | None = None
    config_json: dict | None = None
    english_prompt: str | None = None


class DeployRequest(BaseModel):
    mode: str = "simulation"


class GenerateCodeRequest(BaseModel):
    english: str = Field(..., min_length=5, max_length=4000)
    name: str = Field(default="My Strategy", max_length=200)


@router.get("/cloud/status")
def cloud_status():
    return {
        "host": HOST,
        "environment": settings.environment,
        "is_railway": settings.is_railway,
        "region": settings.cloud_region,
        "worker_required": True,
        "message": "Strategy execution runs on Railway cloud workers, not your device.",
        "gemini_configured": bool(settings.gemini_api_key),
    }


@router.post("/strategies/parse")
def parse_strategy(body: ParseStrategyRequest, db: Session = Depends(get_db)):
    user = ensure_demo_user(db)
    try:
        config = english_to_strategy_config(body.english)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Could not parse strategy: {exc}") from exc

    strategy = Strategy(
        user_id=user.id,
        name=body.name,
        english_prompt=body.english,
        config_json=config.model_dump(),
        status="draft",
    )
    db.add(strategy)
    db.add(
        ExecutionLog(
            strategy_id=strategy.id,
            level="info",
            message="Strategy parsed via Gemini (backend-only)",
            meta={"config": config.model_dump()},
        )
    )
    db.commit()
    db.refresh(strategy)
    return {
        "strategy": _strategy_dict(strategy),
        "config": config.model_dump(),
        "ai_source": "gemini" if settings.gemini_api_key else "fallback",
    }


@router.post("/strategies/generate-code")
def generate_code(body: GenerateCodeRequest, db: Session = Depends(get_db)):
    """Generate full Python trading strategy code from English description."""
    user = ensure_demo_user(db)
    try:
        python_code = english_to_python_code(body.english)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Could not generate code: {exc}") from exc

    strategy = Strategy(
        user_id=user.id,
        name=body.name,
        english_prompt=body.english,
        config_json={"code": python_code, "language": "python", "type": "full"},
        status="draft",
    )
    db.add(strategy)
    db.add(
        ExecutionLog(
            strategy_id=strategy.id,
            level="info",
            message="Full Python code generated via Gemini AI",
            meta={"lines_of_code": len(python_code.split("\n"))},
        )
    )
    db.commit()
    db.refresh(strategy)

    return {
        "strategy": _strategy_dict(strategy),
        "code": python_code,
        "language": "python",
        "ai_source": "gemini" if settings.gemini_api_key else "fallback",
    }


@router.post("/strategies/{strategy_id}/execute-code")
def execute_code(strategy_id: str, db: Session = Depends(get_db)):
    """Execute the generated Python code and return results."""
    s = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not s:
        raise HTTPException(404, "Strategy not found")

    code_data = s.config_json
    if code_data.get("language") != "python" or "code" not in code_data:
        raise HTTPException(400, "Strategy does not have generated Python code")

    python_code = code_data["code"]
    
    result = execute_strategy_code(python_code)

    if result.get("success"):
        db.add(
            ExecutionLog(
                strategy_id=s.id,
                level="info",
                message=f"Code executed: {result.get('total_trades', 0)} trades, P&L: {result.get('final_pnl', 0):.2f}",
                meta=result,
            )
        )
    else:
        db.add(
            ExecutionLog(
                strategy_id=s.id,
                level="error",
                message=f"Execution failed: {result.get('error')}",
                meta=result,
            )
        )
    db.commit()

    return {
        "strategy_id": strategy_id,
        "execution": result,
    }


@router.get("/strategies")
def list_strategies(db: Session = Depends(get_db)):
    ensure_demo_user(db)
    rows = db.query(Strategy).order_by(Strategy.updated_at.desc()).all()
    return {"strategies": [_strategy_dict(s) for s in rows]}


@router.get("/strategies/{strategy_id}")
def get_strategy(strategy_id: str, db: Session = Depends(get_db)):
    s = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not s:
        raise HTTPException(404, "Strategy not found")
    return {"strategy": _strategy_dict(s)}


@router.patch("/strategies/{strategy_id}")
def update_strategy(strategy_id: str, body: StrategyUpdateRequest, db: Session = Depends(get_db)):
    s = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not s:
        raise HTTPException(404, "Strategy not found")
    if body.name:
        s.name = body.name
    if body.english_prompt:
        s.english_prompt = body.english_prompt
        config = english_to_strategy_config(body.english_prompt)
        s.config_json = config.model_dump()
    if body.config_json:
        s.config_json = StrategyConfig.model_validate(body.config_json).model_dump()
    s.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(s)
    return {"strategy": _strategy_dict(s)}


@router.post("/strategies/{strategy_id}/backtest")
def run_strategy_backtest(strategy_id: str, db: Session = Depends(get_db)):
    s = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not s:
        raise HTTPException(404, "Strategy not found")
    config = StrategyConfig.model_validate(s.config_json)
    result = run_backtest(config)
    report = BacktestReport(
        strategy_id=s.id,
        metrics=result["metrics"],
        equity_curve=result["equity_curve"],
        drawdown_curve=result["drawdown_curve"],
        trades=result["trades"],
    )
    db.add(report)
    db.add(
        ExecutionLog(
            strategy_id=s.id,
            level="info",
            message=f"Backtest completed: {result['metrics']['num_trades']} trades",
            meta=result["metrics"],
        )
    )
    db.commit()
    db.refresh(report)
    return {"report": _report_dict(report)}


@router.get("/strategies/{strategy_id}/backtests")
def list_backtests(strategy_id: str, db: Session = Depends(get_db)):
    rows = (
        db.query(BacktestReport)
        .filter(BacktestReport.strategy_id == strategy_id)
        .order_by(BacktestReport.created_at.desc())
        .all()
    )
    return {"reports": [_report_dict(r) for r in rows]}


@router.get("/backtests/{report_id}")
def get_backtest(report_id: str, db: Session = Depends(get_db)):
    r = db.query(BacktestReport).filter(BacktestReport.id == report_id).first()
    if not r:
        raise HTTPException(404, "Report not found")
    return {"report": _report_dict(r)}


@router.post("/strategies/{strategy_id}/deploy")
def deploy_strategy(strategy_id: str, body: DeployRequest, db: Session = Depends(get_db)):
    s = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not s:
        raise HTTPException(404, "Strategy not found")

    dep = Deployment(
        strategy_id=s.id,
        mode=body.mode,
        status="running",
        host=HOST,
        started_at=datetime.utcnow(),
        last_price=85.0,
    )
    s.status = "active"
    db.add(dep)
    db.add(
        ExecutionLog(
            deployment_id=dep.id,
            strategy_id=s.id,
            level="info",
            message=f"Deployed to cloud worker on {HOST}",
            meta={"mode": body.mode},
        )
    )
    db.commit()
    db.refresh(dep)
    return {"deployment": _deployment_dict(dep)}


@router.get("/deployments")
def list_deployments(db: Session = Depends(get_db)):
    rows = db.query(Deployment).order_by(Deployment.created_at.desc()).all()
    return {"deployments": [_deployment_dict(d) for d in rows]}


@router.get("/deployments/{deployment_id}")
def get_deployment(deployment_id: str, db: Session = Depends(get_db)):
    d = db.query(Deployment).filter(Deployment.id == deployment_id).first()
    if not d:
        raise HTTPException(404, "Deployment not found")
    trades = (
        db.query(LiveTrade)
        .filter(LiveTrade.deployment_id == deployment_id)
        .order_by(LiveTrade.created_at.desc())
        .limit(50)
        .all()
    )
    return {
        "deployment": _deployment_dict(d),
        "trades": [_trade_dict(t) for t in trades],
    }


@router.post("/deployments/{deployment_id}/stop")
def stop_deployment(deployment_id: str, db: Session = Depends(get_db)):
    d = db.query(Deployment).filter(Deployment.id == deployment_id).first()
    if not d:
        raise HTTPException(404, "Deployment not found")
    d.status = "stopped"
    d.stopped_at = datetime.utcnow()
    clear_state(deployment_id)
    db.add(
        ExecutionLog(
            deployment_id=d.id,
            strategy_id=d.strategy_id,
            level="info",
            message="Deployment stopped from API",
        )
    )
    db.commit()
    return {"deployment": _deployment_dict(d)}


@router.get("/logs")
def get_logs(
    deployment_id: str | None = None,
    strategy_id: str | None = None,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    q = db.query(ExecutionLog).order_by(ExecutionLog.created_at.desc())
    if deployment_id:
        q = q.filter(ExecutionLog.deployment_id == deployment_id)
    if strategy_id:
        q = q.filter(ExecutionLog.strategy_id == strategy_id)
    rows = q.limit(min(limit, 500)).all()
    return {
        "logs": [
            {
                "id": l.id,
                "deployment_id": l.deployment_id,
                "strategy_id": l.strategy_id,
                "level": l.level,
                "message": l.message,
                "meta": l.meta,
                "created_at": l.created_at.isoformat(),
            }
            for l in rows
        ]
    }


def _strategy_dict(s: Strategy) -> dict:
    return {
        "id": s.id,
        "name": s.name,
        "english_prompt": s.english_prompt,
        "config_json": s.config_json,
        "status": s.status,
        "created_at": s.created_at.isoformat(),
        "updated_at": s.updated_at.isoformat(),
    }


def _report_dict(r: BacktestReport) -> dict:
    return {
        "id": r.id,
        "strategy_id": r.strategy_id,
        "metrics": r.metrics,
        "equity_curve": r.equity_curve,
        "drawdown_curve": r.drawdown_curve,
        "trades": r.trades,
        "created_at": r.created_at.isoformat(),
    }


def _deployment_dict(d: Deployment) -> dict:
    return {
        "id": d.id,
        "strategy_id": d.strategy_id,
        "mode": d.mode,
        "status": d.status,
        "host": d.host,
        "running_pnl": d.running_pnl,
        "open_position": d.open_position,
        "position_qty": d.position_qty,
        "entry_price": d.entry_price,
        "last_price": d.last_price,
        "tick_count": d.tick_count,
        "started_at": d.started_at.isoformat() if d.started_at else None,
        "stopped_at": d.stopped_at.isoformat() if d.stopped_at else None,
        "created_at": d.created_at.isoformat(),
    }


def _trade_dict(t: LiveTrade) -> dict:
    return {
        "id": t.id,
        "side": t.side,
        "price": t.price,
        "quantity": t.quantity,
        "pnl": t.pnl,
        "created_at": t.created_at.isoformat(),
    }
