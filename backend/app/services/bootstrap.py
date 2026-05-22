"""Seed default demo user."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import User


def ensure_demo_user(db: Session) -> User:
    user = db.query(User).filter(User.email == "demo@cloudtrade.app").first()
    if user:
        return user
    user = User(email="demo@cloudtrade.app", name="Demo Trader")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
