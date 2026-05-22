"""
Railway cloud worker — continuous strategy execution loops.

Run as separate Railway service:
  python -m app.workers.live_worker

This process NEVER runs on the user's laptop in production.
"""

from __future__ import annotations

import os
import socket
import time
from datetime import datetime

from app.config import get_settings
from app.database import SessionLocal, init_db
from app.engines.live_engine import clear_state, process_tick
from app.engines.strategy_schema import StrategyConfig
from sqlalchemy.orm import joinedload

from app.models import Deployment, ExecutionLog, LiveTrade, Strategy

settings = get_settings()
HOST = socket.gethostname()
WORKER_ID = os.getenv("RAILWAY_REPLICA_ID", HOST)


def log(db, deployment_id: str, strategy_id: str, level: str, message: str, meta: dict | None = None):
    db.add(
        ExecutionLog(
            deployment_id=deployment_id,
            strategy_id=strategy_id,
            level=level,
            message=message,
            meta=meta or {},
        )
    )


def run_loop() -> None:
    init_db()
    print(f"[worker] CloudTrade worker started on {HOST} (id={WORKER_ID})")
    poll = settings.worker_poll_seconds

    while True:
        db = SessionLocal()
        try:
            running = (
                db.query(Deployment)
                .options(joinedload(Deployment.strategy))
                .filter(Deployment.status == "running")
                .all()
            )
            for dep in running:
                strategy = dep.strategy or db.query(Strategy).filter(Strategy.id == dep.strategy_id).first()
                if not strategy:
                    continue
                try:
                    config = StrategyConfig.model_validate(strategy.config_json)
                except Exception as exc:
                    dep.status = "error"
                    log(db, dep.id, dep.strategy_id, "error", f"Invalid config: {exc}")
                    db.commit()
                    continue

                result = process_tick(
                    config,
                    dep.id,
                    dep.last_price,
                    dep.tick_count,
                    dep.open_position,
                    dep.entry_price,
                )
                dep.last_price = result["price"]
                dep.tick_count += 1

                for ev in result["events"]:
                    if ev["type"] == "buy":
                        dep.open_position = True
                        dep.entry_price = ev["price"]
                        dep.position_qty = config.quantity
                        log(
                            db,
                            dep.id,
                            dep.strategy_id,
                            "trade",
                            f"BUY @ {ev['price']}",
                            ev,
                        )
                        db.add(
                            LiveTrade(
                                deployment_id=dep.id,
                                side="buy",
                                price=ev["price"],
                                quantity=config.quantity,
                            )
                        )
                    elif ev["type"] == "sell":
                        dep.open_position = False
                        dep.running_pnl += ev.get("pnl", 0)
                        dep.entry_price = None
                        log(
                            db,
                            dep.id,
                            dep.strategy_id,
                            "trade",
                            f"SELL @ {ev['price']} PnL {ev.get('pnl', 0)}",
                            ev,
                        )
                        db.add(
                            LiveTrade(
                                deployment_id=dep.id,
                                side="sell",
                                price=ev["price"],
                                quantity=config.quantity,
                                pnl=ev.get("pnl", 0),
                            )
                        )

                if dep.tick_count % 10 == 0:
                    log(
                        db,
                        dep.id,
                        dep.strategy_id,
                        "info",
                        f"Tick {dep.tick_count} price={dep.last_price} pnl={dep.running_pnl:.2f}",
                    )

            db.commit()
        except Exception as exc:
            db.rollback()
            print(f"[worker] error: {exc}")
        finally:
            db.close()

        time.sleep(poll)


if __name__ == "__main__":
    run_loop()
