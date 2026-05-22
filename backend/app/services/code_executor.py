"""Safe code execution for generated trading strategies."""

from __future__ import annotations

import tempfile
import subprocess
import json
from pathlib import Path


def execute_strategy_code(python_code: str, data_csv_path: str | None = None) -> dict:
    """
    Safely execute generated strategy code in an isolated environment.
    
    Args:
        python_code: The full Python strategy code
        data_csv_path: Optional path to CSV file with OHLCV data
    
    Returns:
        Execution results including P&L, trades, equity curve
    """
    
    with tempfile.TemporaryDirectory() as tmpdir:
        script_path = Path(tmpdir) / "strategy.py"
        output_path = Path(tmpdir) / "output.json"
        
        # Add execution wrapper
        wrapped_code = f"""
{python_code}

import json
import pandas as pd
import numpy as np

# Helper functions
def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(prices, fast=12, slow=26):
    ema_fast = prices.ewm(span=fast).mean()
    ema_slow = prices.ewm(span=slow).mean()
    return ema_fast - ema_slow

def calculate_signal_line(macd, period=9):
    return macd.ewm(span=period).mean()

# Load demo data or use provided data
try:
    if "{data_csv_path}":
        df = pd.read_csv("{data_csv_path}")
    else:
        # Default demo data
        df = pd.DataFrame({{
            'close': [100 + i*0.5 + (i % 10 - 5)*2 for i in range(100)],
            'high': [101 + i*0.5 + (i % 10 - 5)*2 for i in range(100)],
            'low': [99 + i*0.5 + (i % 10 - 5)*2 for i in range(100)],
            'open': [100.5 + i*0.5 + (i % 10 - 5)*2 for i in range(100)],
            'volume': [1000000 for i in range(100)],
        }})
    
    strategy = UserStrategy()
    result = strategy.execute(df)
    
    with open("{output_path}", "w") as f:
        json.dump({{
            'success': True,
            'final_pnl': float(result.get('final_pnl', 0)),
            'total_trades': int(result.get('total_trades', 0)),
            'equity_curve': [float(x) for x in result.get('equity_curve', [1.0])],
            'trades': result.get('trades', []),
            'symbol': result.get('symbol', 'YESBANK'),
        }}, f)
except Exception as e:
    with open("{output_path}", "w") as f:
        json.dump({{
            'success': False,
            'error': str(e),
        }}, f)
"""
        
        script_path.write_text(wrapped_code)
        
        try:
            # Run in isolated process with timeout
            result = subprocess.run(
                ["python", str(script_path)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            
            # Read output
            if output_path.exists():
                output = json.loads(output_path.read_text())
                return output
            else:
                return {
                    "success": False,
                    "error": f"Execution failed: {result.stderr}",
                }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Code execution timeout (30s limit)",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
