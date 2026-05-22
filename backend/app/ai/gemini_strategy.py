"""Backend-only Gemini: English strategy → validated StrategyConfig JSON."""

from __future__ import annotations

import json
import re

from app.config import get_settings
from app.engines.strategy_schema import GEMINI_JSON_SCHEMA_HINT, StrategyConfig

settings = get_settings()


def _parse_json_from_text(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        text = text[start : end + 1]
    return json.loads(text)


def _fallback_config(english: str) -> dict:
    """Rule-based fallback when Gemini unavailable."""
    lower = english.lower()
    if "macd" in lower:
        return {
            "strategy_type": "MACD",
            "symbol": "YESBANK",
            "buy_condition": "crosses_above",
            "buy_value": 0,
            "sell_condition": "crosses_below",
            "sell_value": 0,
            "quantity": 1,
            "fast_period": 12,
            "slow_period": 26,
            "signal_period": 9,
        }
    if "sma" in lower or "moving average" in lower:
        return {
            "strategy_type": "SMA_CROSS",
            "symbol": "YESBANK",
            "buy_condition": "crosses_above",
            "buy_value": 0,
            "sell_condition": "crosses_below",
            "sell_value": 0,
            "quantity": 1,
            "sma_fast": 10,
            "sma_slow": 30,
        }
    if "09:" in lower or "time" in lower:
        return {
            "strategy_type": "TIME_BASED",
            "symbol": "YESBANK",
            "buy_condition": "below",
            "buy_value": 0,
            "sell_condition": "above",
            "sell_value": 0,
            "quantity": 1,
            "buy_time": "09:15",
            "sell_time": "09:35",
        }
    buy_val, sell_val = 30.0, 70.0
    nums = [float(n) for n in re.findall(r"\d+(?:\.\d+)?", english)]
    if len(nums) >= 2:
        buy_val, sell_val = nums[0], nums[1]
    return {
        "strategy_type": "RSI",
        "symbol": "YESBANK",
        "buy_condition": "below",
        "buy_value": buy_val,
        "sell_condition": "above",
        "sell_value": sell_val,
        "quantity": 1,
    }


def english_to_strategy_config(english: str) -> StrategyConfig:
    """Convert plain English to validated strategy config via Gemini API."""
    if not settings.gemini_api_key:
        return StrategyConfig.model_validate(_fallback_config(english))

    import google.generativeai as genai

    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(settings.gemini_model)

    prompt = f"""You are a trading strategy parser for Indian equities.
Convert the user's strategy into structured JSON for backtesting and simulation.
Use RSI for oversold/overbought language, MACD for MACD, SMA_CROSS for moving averages, TIME_BASED for time schedules.

User strategy:
{english}

{GEMINI_JSON_SCHEMA_HINT}
"""
    response = model.generate_content(
        prompt,
        generation_config={"temperature": 0.1, "max_output_tokens": 1024},
    )
    raw = response.text or "{}"
    data = _parse_json_from_text(raw)
    return StrategyConfig.model_validate(data)
