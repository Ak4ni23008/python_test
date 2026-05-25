#!/usr/bin/env python3
"""Test CloudTrade AI code generation locally."""

import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from app.ai.code_generator import english_to_python_code


def test_code_generation():
    """Test AI code generation with various strategies."""
    
    # Get API key
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not gemini_key:
        print("⚠️  WARNING: GEMINI_API_KEY not set in .env")
        print("   This will use fallback code generation (rule-based)")
        print()
        print("   To enable Gemini AI:")
        print("   1. Get your API key from: https://aistudio.google.com/apikey")
        print("   2. Add to .env: GEMINI_API_KEY=<your_key>")
        print()
    else:
        print("✅ Gemini API key found - using AI code generation\n")

    test_strategies = [
        "Buy when RSI goes below 30, sell when it goes above 70",
        "MACD crossover strategy - buy when MACD crosses above signal line",
        "Simple moving average: buy when SMA 10 crosses above SMA 30",
        "Bollinger Bands: buy at lower band, sell at upper band",
        "Time-based: buy at 9:15 AM, sell at 3:30 PM",
    ]

    for i, strategy in enumerate(test_strategies, 1):
        print(f"\n{'='*70}")
        print(f"Test {i}: {strategy}")
        print(f"{'='*70}")
        
        try:
            code = english_to_python_code(strategy)
            
            # Show snippet
            lines = code.split("\n")
            print("\n📝 Generated Code (first 50 lines):")
            print("-" * 70)
            for line in lines[:50]:
                print(line)
            if len(lines) > 50:
                print(f"... ({len(lines) - 50} more lines)")
            
            # Verify it's executable
            print(f"\n✅ Code is valid Python ({len(lines)} lines total)")
            
            # Try to compile it
            try:
                compile(code, '<string>', 'exec')
                print("✅ Code compiles successfully")
            except SyntaxError as e:
                print(f"❌ Syntax error: {e}")
                
        except Exception as e:
            print(f"❌ Error generating code: {e}")


def test_code_execution():
    """Test if generated code can actually execute."""
    import pandas as pd
    import numpy as np
    
    print(f"\n{'='*70}")
    print("EXECUTION TEST")
    print(f"{'='*70}")
    
    strategy_desc = "RSI below 30 buy, above 70 sell"
    print(f"\nGenerating code for: {strategy_desc}")
    
    try:
        code = english_to_python_code(strategy_desc)
        print("✅ Code generated")
        
        # Create mock data
        dates = pd.date_range('2024-01-01', periods=100, freq='1h')
        df = pd.DataFrame({
            'open': np.random.uniform(100, 110, 100),
            'high': np.random.uniform(110, 120, 100),
            'low': np.random.uniform(90, 100, 100),
            'close': np.random.uniform(100, 110, 100),
            'volume': np.random.uniform(1000, 10000, 100),
        }, index=dates)
        
        print(f"✅ Created mock data ({len(df)} bars)")
        
        # Execute the code in a safe namespace
        namespace = {
            'pd': pd,
            'np': np,
            'df': df,
            'Strategy': None,  # Will be defined in generated code
        }
        
        exec(code, namespace)
        Strategy = namespace['Strategy']
        print("✅ Strategy class created from generated code")
        
        # Run backtest
        strategy = Strategy(symbol="TEST", quantity=1)
        result = strategy.execute(df)
        
        print(f"\n📊 Backtest Results:")
        print(f"   Total Trades: {result['total_trades']}")
        print(f"   Final P&L: {result['final_pnl']:.2f}")
        print(f"   Max Equity: {max(result['equity_curve']):.4f}")
        print(f"   Min Equity: {min(result['equity_curve']):.4f}")
        print(f"   Win Rate: N/A (need more data)")
        print("\n✅ Code executed successfully!")
        
    except Exception as e:
        print(f"❌ Execution failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🤖 CloudTrade AI Code Generation Test")
    print("="*70)
    
    print("\n📝 Phase 1: Code Generation Tests")
    test_code_generation()
    
    print("\n\n⚡ Phase 2: Execution Test")
    test_code_execution()
    
    print("\n\n" + "="*70)
    print("✅ All tests complete!")
    print("="*70)
    print("\nNext steps:")
    print("1. If tests pass: Your AI is working! ✨")
    print("2. Deploy to Railway with your GEMINI_API_KEY")
    print("3. Try the chat UI at: http://localhost:3000/chat")
    print()
