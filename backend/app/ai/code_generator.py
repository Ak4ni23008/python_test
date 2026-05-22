"""Full Python strategy code generation from English using Gemini AI."""

from __future__ import annotations

import re

from app.config import get_settings

settings = get_settings()

STRATEGY_BASE_CLASS = '''"""Auto-generated trading strategy."""
from typing import Dict, List
import pandas as pd
import numpy as np

class Strategy:
    """Base trading strategy class."""
    
    def __init__(self, symbol: str, quantity: int = 1):
        self.symbol = symbol
        self.quantity = quantity
        self.position = 0
        self.entry_price = None
        self.trades = []
        
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators. Override in subclass."""
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate buy/sell signals. Override in subclass."""
        df['signal'] = 0
        return df
    
    def execute(self, df: pd.DataFrame) -> Dict:
        """Execute strategy on OHLCV data."""
        df = self.calculate_indicators(df)
        df = self.generate_signals(df)
        
        pnl = 0
        equity_curve = [1.0]
        
        for idx, row in df.iterrows():
            signal = row.get('signal', 0)
            price = row['close']
            
            # Buy signal
            if signal == 1 and self.position == 0:
                self.entry_price = price
                self.position = self.quantity
                self.trades.append({
                    'type': 'BUY',
                    'price': price,
                    'qty': self.quantity,
                    'time': row.get('time', idx)
                })
            
            # Sell signal
            elif signal == -1 and self.position > 0:
                exit_price = price
                trade_pnl = (exit_price - self.entry_price) * self.position
                pnl += trade_pnl
                self.trades.append({
                    'type': 'SELL',
                    'price': exit_price,
                    'qty': self.position,
                    'pnl': trade_pnl,
                    'time': row.get('time', idx)
                })
                self.position = 0
                self.entry_price = None
            
            # Update P&L curve
            if self.position > 0:
                unrealized = (price - self.entry_price) * self.position
                equity_curve.append(1.0 + (pnl + unrealized) / 100000)
            else:
                equity_curve.append(1.0 + pnl / 100000)
        
        return {
            'trades': self.trades,
            'final_pnl': pnl,
            'equity_curve': equity_curve,
            'total_trades': len([t for t in self.trades if t['type'] == 'BUY']),
            'symbol': self.symbol,
            'quantity': self.quantity
        }
'''

CODE_TEMPLATE = '''"""Auto-generated trading strategy from: {description}"""
{base_class}

class UserStrategy(Strategy):
    """User-defined strategy: {description}"""
    
    def __init__(self, symbol: str = "YESBANK", quantity: int = 1):
        super().__init__(symbol, quantity)
        self.config = {
            'symbol': symbol,
            'quantity': quantity,
        }
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators."""
{indicators_code}
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate buy/sell signals."""
{signals_code}
        return df

# Execution example
if __name__ == "__main__":
    import pandas as pd
    # Load your OHLCV data
    # df = pd.read_csv("data.csv")
    # strategy = UserStrategy()
    # result = strategy.execute(df)
    # print(f"Final P&L: {{result['final_pnl']}}")
'''


def english_to_python_code(english: str) -> str:
    """Convert plain English strategy to full Python code using Gemini."""
    if not settings.gemini_api_key:
        return _fallback_code(english)

    import google.generativeai as genai

    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(settings.gemini_model)

    prompt = f"""You are an expert Python trader. Convert this English trading strategy into production-ready Python code.

Strategy description:
{english}

Requirements:
1. Generate TWO separate code blocks:
   - First: Python code for calculate_indicators() method (indent with 8 spaces)
   - Second: Python code for generate_signals() method (indent with 8 spaces)

2. Use pandas (df) and numpy (np)
3. For indicators (RSI, MACD, SMA, Bollinger Bands, etc.):
   - Add new columns to df: df['rsi'], df['macd'], df['sma_20'], etc.
4. For signals:
   - Set df['signal'] = 1 for BUY, -1 for SELL, 0 for HOLD
   - Use the calculated indicators

5. Output format EXACTLY:
INDICATORS_START
<python code for indicators here>
INDICATORS_END

SIGNALS_START
<python code for signals here>
SIGNALS_END

Example for "RSI below 30 buy, above 70 sell":
INDICATORS_START
        df['rsi'] = calculate_rsi(df['close'], period=14)
INDICATORS_END

SIGNALS_START
        df['signal'] = 0
        df.loc[df['rsi'] < 30, 'signal'] = 1
        df.loc[df['rsi'] > 70, 'signal'] = -1
SIGNALS_END

Now generate code for: {english}
"""

    response = model.generate_content(
        prompt,
        generation_config={"temperature": 0.3, "max_output_tokens": 2048},
    )

    raw = response.text or ""
    indicators = _extract_section(raw, "INDICATORS_START", "INDICATORS_END")
    signals = _extract_section(raw, "SIGNALS_START", "SIGNALS_END")

    if not indicators:
        indicators = "        df['rsi'] = calculate_rsi(df['close'], period=14)\n"
    if not signals:
        signals = "        df['signal'] = 0\n        df.loc[df['rsi'] < 30, 'signal'] = 1\n        df.loc[df['rsi'] > 70, 'signal'] = -1\n"

    code = CODE_TEMPLATE.format(
        description=english,
        base_class=STRATEGY_BASE_CLASS,
        indicators_code=indicators,
        signals_code=signals,
    )

    return code


def _extract_section(text: str, start_marker: str, end_marker: str) -> str:
    """Extract code section between markers."""
    start = text.find(start_marker)
    end = text.find(end_marker)
    if start < 0 or end < 0:
        return ""
    return text[start + len(start_marker) : end].strip()


def _fallback_code(english: str) -> str:
    """Generate fallback code when Gemini unavailable."""
    lower = english.lower()

    indicators = "        df['rsi'] = calculate_rsi(df['close'], period=14)\n"
    signals = (
        "        df['signal'] = 0\n"
        "        df.loc[df['rsi'] < 30, 'signal'] = 1\n"
        "        df.loc[df['rsi'] > 70, 'signal'] = -1\n"
    )

    if "macd" in lower:
        indicators = (
            "        df['macd'] = calculate_macd(df['close'], fast=12, slow=26)\n"
            "        df['signal_line'] = calculate_signal_line(df['macd'], period=9)\n"
        )
        signals = (
            "        df['signal'] = 0\n"
            "        df.loc[df['macd'] > df['signal_line'], 'signal'] = 1\n"
            "        df.loc[df['macd'] < df['signal_line'], 'signal'] = -1\n"
        )
    elif "sma" in lower or "moving average" in lower:
        indicators = (
            "        df['sma_10'] = df['close'].rolling(10).mean()\n"
            "        df['sma_30'] = df['close'].rolling(30).mean()\n"
        )
        signals = (
            "        df['signal'] = 0\n"
            "        df.loc[df['sma_10'] > df['sma_30'], 'signal'] = 1\n"
            "        df.loc[df['sma_10'] < df['sma_30'], 'signal'] = -1\n"
        )

    code = CODE_TEMPLATE.format(
        description=english,
        base_class=STRATEGY_BASE_CLASS,
        indicators_code=indicators,
        signals_code=signals,
    )

    return code
