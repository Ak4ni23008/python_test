"""Full Python strategy code generation from English using Gemini AI."""

from __future__ import annotations

import re

from app.config import get_settings

settings = get_settings()

STRATEGY_BASE_CLASS = '''"""Auto-generated trading strategy."""
from typing import Dict, List
import pandas as pd
import numpy as np


# Built-in indicator functions
def calculate_rsi(prices, period=14):
    """Calculate RSI indicator."""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_macd(prices, fast=12, slow=26, signal=9):
    """Calculate MACD indicator."""
    macd = prices.ewm(span=fast).mean() - prices.ewm(span=slow).mean()
    return macd


def calculate_signal_line(macd, period=9):
    """Calculate MACD signal line."""
    return macd.ewm(span=period).mean()


def calculate_bb(prices, period=20, std_dev=2):
    """Calculate Bollinger Bands."""
    sma = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)
    return sma, upper_band, lower_band


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

    prompt = f"""You are an expert Python algorithmic trader. Your task is to convert a plain English trading strategy description into PRODUCTION-READY Python code.

IMPORTANT: Generate TWO separate code blocks - indicators and signals ONLY. Do NOT generate classes or functions, only code that operates on the dataframe.

Input Strategy:
"{english}"

Your output MUST follow this EXACT format:

INDICATORS_START
<8-space indented Python code for calculate_indicators method>
INDICATORS_END

SIGNALS_START
<8-space indented Python code for generate_signals method>
SIGNALS_END

GUIDELINES:
1. Available built-in indicators (already in base class):
   - calculate_rsi(prices, period=14) → returns RSI values
   - calculate_macd(prices, fast=12, slow=26) → returns MACD line
   - calculate_signal_line(macd, period=9) → returns signal line
   - calculate_bb(prices, period=20, std_dev=2) → returns (sma, upper, lower)

2. For INDICATORS section:
   - Calculate any indicators needed
   - Add new columns to df: df['rsi'], df['macd'], df['sma_20'], etc.
   - Use df['close'], df['high'], df['low'], df['volume'] as inputs
   - Indent with 8 spaces (method body level)

3. For SIGNALS section:
   - Set df['signal'] values: 1=BUY, -1=SELL, 0=HOLD/NO_SIGNAL
   - Use the indicators you calculated
   - Start with: df['signal'] = 0
   - Use conditions like: df.loc[condition, 'signal'] = 1
   - Avoid multiple contradicting signals in same bar

4. Production requirements:
   - Handle NaN/missing values gracefully
   - Use vectorized pandas operations (NOT loops)
   - Return df at end
   - No external dependencies beyond pandas/numpy
   - Include realistic risk management (optional)

5. Example (RSI strategy):
INDICATORS_START
        df['rsi'] = calculate_rsi(df['close'], period=14)
INDICATORS_END

SIGNALS_START
        df['signal'] = 0
        df.loc[df['rsi'] < 30, 'signal'] = 1
        df.loc[df['rsi'] > 70, 'signal'] = -1
SIGNALS_END

Now generate code for: {english}

REMEMBER:
- Output MUST have both INDICATORS_START/END and SIGNALS_START/END
- Indent method body with 8 spaces
- Use only available indicators and pandas/numpy operations
- Make it production-ready and backtestable"""

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
    """Generate fallback code when Gemini unavailable - intelligently detects strategy type."""
    lower = english.lower()

    # RSI Strategy (most common)
    if "rsi" in lower:
        buy = 30.0
        sell = 70.0
        nums = [float(n) for n in re.findall(r"\d+(?:\.\d+)?", english)]
        if len(nums) >= 2:
            buy, sell = nums[0], nums[1]
        indicators = f"        df['rsi'] = calculate_rsi(df['close'], period=14)\n"
        signals = (
            f"        df['signal'] = 0\n"
            f"        df.loc[df['rsi'] < {buy}, 'signal'] = 1\n"
            f"        df.loc[df['rsi'] > {sell}, 'signal'] = -1\n"
        )
    # MACD Strategy
    elif "macd" in lower:
        indicators = (
            "        df['macd'] = calculate_macd(df['close'], fast=12, slow=26)\n"
            "        df['signal_line'] = calculate_signal_line(df['macd'], period=9)\n"
        )
        signals = (
            "        df['signal'] = 0\n"
            "        df.loc[df['macd'] > df['signal_line'], 'signal'] = 1\n"
            "        df.loc[df['macd'] < df['signal_line'], 'signal'] = -1\n"
        )
    # SMA/Moving Average Crossover
    elif "sma" in lower or "moving average" in lower or "cross" in lower:
        indicators = (
            "        df['sma_10'] = df['close'].rolling(10).mean()\n"
            "        df['sma_30'] = df['close'].rolling(30).mean()\n"
        )
        signals = (
            "        df['signal'] = 0\n"
            "        df.loc[df['sma_10'] > df['sma_30'], 'signal'] = 1\n"
            "        df.loc[df['sma_10'] < df['sma_30'], 'signal'] = -1\n"
        )
    # Bollinger Bands
    elif "bollinger" in lower or "band" in lower:
        indicators = (
            "        df['bb_mid'], df['bb_upper'], df['bb_lower'] = calculate_bb(df['close'], period=20, std_dev=2)\n"
        )
        signals = (
            "        df['signal'] = 0\n"
            "        df.loc[df['close'] < df['bb_lower'], 'signal'] = 1\n"
            "        df.loc[df['close'] > df['bb_upper'], 'signal'] = -1\n"
        )
    # Time-based strategy
    elif "time" in lower or ":" in english:
        indicators = "        # Time-based strategy (no indicators needed)\n"
        signals = (
            "        df['signal'] = 0\n"
            "        df['hour'] = pd.to_datetime(df.index).hour\n"
            "        df['minute'] = pd.to_datetime(df.index).minute\n"
            "        df.loc[(df['hour'] == 9) & (df['minute'] <= 15), 'signal'] = 1\n"
            "        df.loc[(df['hour'] == 15) & (df['minute'] >= 0), 'signal'] = -1\n"
        )
    # Default: RSI
    else:
        indicators = "        df['rsi'] = calculate_rsi(df['close'], period=14)\n"
        signals = (
            "        df['signal'] = 0\n"
            "        df.loc[df['rsi'] < 30, 'signal'] = 1\n"
            "        df.loc[df['rsi'] > 70, 'signal'] = -1\n"
        )

    code = CODE_TEMPLATE.format(
        description=english,
        base_class=STRATEGY_BASE_CLASS,
        indicators_code=indicators,
        signals_code=signals,
    )

    return code
