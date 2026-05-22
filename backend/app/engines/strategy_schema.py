"""Validated strategy configuration — safe template input only."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

StrategyType = Literal["RSI", "MACD", "SMA_CROSS", "TIME_BASED"]
Condition = Literal["below", "above", "crosses_below", "crosses_above"]


class StrategyConfig(BaseModel):
    strategy_type: StrategyType
    symbol: str = Field(default="YESBANK", max_length=32)
    buy_condition: Condition = "below"
    buy_value: float = Field(ge=0, le=1000)
    sell_condition: Condition = "above"
    sell_value: float = Field(ge=0, le=1000)
    quantity: int = Field(default=1, ge=1, le=10000)
    fast_period: int = Field(default=12, ge=2, le=200)
    slow_period: int = Field(default=26, ge=2, le=200)
    signal_period: int = Field(default=9, ge=2, le=50)
    sma_fast: int = Field(default=10, ge=2, le=200)
    sma_slow: int = Field(default=30, ge=2, le=200)
    buy_time: str = Field(default="09:15", pattern=r"^\d{2}:\d{2}$")
    sell_time: str = Field(default="09:35", pattern=r"^\d{2}:\d{2}$")

    @field_validator("sell_value")
    @classmethod
    def rsi_sell_above_buy(cls, v: float, info) -> float:
        return v

    model_config = {"extra": "forbid"}


GEMINI_JSON_SCHEMA_HINT = """
Return ONLY valid JSON matching this schema (no markdown):
{
  "strategy_type": "RSI" | "MACD" | "SMA_CROSS" | "TIME_BASED",
  "symbol": "YESBANK",
  "buy_condition": "below" | "above" | "crosses_below" | "crosses_above",
  "buy_value": number,
  "sell_condition": "below" | "above" | "crosses_below" | "crosses_above",
  "sell_value": number,
  "quantity": 1,
  "fast_period": 12,
  "slow_period": 26,
  "signal_period": 9,
  "sma_fast": 10,
  "sma_slow": 30,
  "buy_time": "09:15",
  "sell_time": "09:35"
}
"""
