# 🤖 Full AI Code Generation - CloudTrade

## Overview

CloudTrade now includes **full Python code generation** from English descriptions using Google Gemini AI. Users can describe their trading strategies in plain English, and the AI generates **production-ready Python code** that can be deployed immediately.

## How It Works

### 1. **English Strategy Description** → AI Parsing
User enters: `"Buy when RSI crosses below 30, sell when it crosses above 70"`

### 2. **Gemini AI Code Generation**
The backend sends to Gemini:
- Strategy description
- Prompt asking for:
  - Indicator calculations (RSI, MACD, SMA, etc.)
  - Buy/sell signal generation
  - Position management logic

### 3. **Generated Python Code**
Gemini returns structured Python code with:
```python
class UserStrategy(Strategy):
    def calculate_indicators(self, df):
        # Auto-generated indicator code
        df['rsi'] = calculate_rsi(df['close'], period=14)
    
    def generate_signals(self, df):
        # Auto-generated signal logic
        df['signal'] = 0
        df.loc[df['rsi'] < 30, 'signal'] = 1
        df.loc[df['rsi'] > 70, 'signal'] = -1
```

### 4. **Execution & Results**
- Code is executed in isolated subprocess (30s timeout)
- Returns backtest results: P&L, equity curve, trades
- Can be deployed to Railway workers

## API Endpoints

### Generate Full Python Code
```http
POST /api/strategies/generate-code
Content-Type: application/json

{
  "english": "Buy when RSI crosses below 30, sell when RSI crosses above 70",
  "name": "RSI Mean Reversion"
}
```

**Response:**
```json
{
  "strategy": {
    "id": "uuid",
    "name": "RSI Mean Reversion",
    "english_prompt": "Buy when RSI crosses below 30...",
    "status": "draft"
  },
  "code": "class UserStrategy(Strategy): ...",
  "language": "python",
  "ai_source": "gemini"
}
```

### Execute Generated Code
```http
POST /api/strategies/{strategy_id}/execute-code
```

**Response:**
```json
{
  "strategy_id": "uuid",
  "execution": {
    "success": true,
    "final_pnl": 5234.50,
    "total_trades": 12,
    "equity_curve": [1.0, 1.001, 1.003, ...],
    "trades": [
      {
        "type": "BUY",
        "price": 95.2,
        "qty": 1,
        "time": "2026-05-22 09:15"
      }
    ]
  }
}
```

## Frontend Chat Interface

### Two Modes

1. **🐍 Full Code Mode** (Default)
   - Generates complete Python strategies
   - Full indicator and signal control
   - For experienced traders
   - Can deploy directly to production

2. **📋 Template Mode**
   - Uses predefined safe templates (RSI, MACD, SMA, TIME_BASED)
   - Faster, simpler configuration
   - Lower risk
   - Good for beginners

### Chat Features

- ✨ Real-time streaming messages
- 📋 Copy code to clipboard
- 🔍 Syntax-highlighted code blocks
- 📊 Direct link to backtest results
- 🐍/📋 Switch between full code and template modes
- ⚡ Instant strategy deployment

## Generated Strategy Structure

Every generated strategy includes:

### Base Class (Automatically Provided)
```python
class Strategy:
    def __init__(self, symbol, quantity=1)
    def calculate_indicators(self, df)
    def generate_signals(self, df)
    def execute(self, df)  # Runs backtest
```

### Auto-Generated User Strategy
```python
class UserStrategy(Strategy):
    def __init__(self, symbol="YESBANK", quantity=1)
    def calculate_indicators(self, df)  # Indicators added by AI
    def generate_signals(self, df)      # Signals added by AI
```

### Helper Functions Available
- `calculate_rsi(prices, period=14)`
- `calculate_macd(prices, fast=12, slow=26)`
- `calculate_signal_line(macd, period=9)`
- And more pandas/numpy helpers

## Safety & Limitations

### Safety Features ✅
- Code runs in **isolated subprocess** (no access to system)
- **30-second timeout** on all executions
- **Sandboxed environment** (no file system access except temp)
- **No arbitrary shell commands** allowed
- Code is **logged and auditable**

### Current Limitations ⚠️
- Max description length: 4000 characters
- Max execution time: 30 seconds
- Requires Gemini API key for full code generation
- Fallback mode uses rule-based templates
- No live trading yet (simulation only)

## Environment Variables

```bash
GEMINI_API_KEY=<your-gemini-api-key>
GEMINI_MODEL=gemini-2.0-flash  # or latest model
```

## Examples

### Example 1: RSI Strategy
**User Input:**
```
"Buy when RSI crosses below 30, sell when RSI crosses above 70"
```

**Generated Code:**
- Calculates 14-period RSI
- Sets signal=1 when RSI<30
- Sets signal=-1 when RSI>70

### Example 2: MACD Strategy
**User Input:**
```
"MACD crossover strategy with fast line 12, slow line 26, signal 9. Buy when MACD crosses above signal line, sell when crosses below"
```

**Generated Code:**
- Calculates MACD (12, 26)
- Calculates Signal Line (9)
- Implements crossover logic

### Example 3: SMA Crossover
**User Input:**
```
"10-day SMA crosses above 30-day SMA, buy. When 10-day crosses below 30-day, sell"
```

**Generated Code:**
- Calculates 10-period SMA
- Calculates 30-period SMA
- Implements crossover signals

## Workflow

```
┌─────────────────────────┐
│   User Chat Input       │
│  (English Strategy)     │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  Gemini AI API Call     │
│  (Generate Python Code) │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  Code Validation        │
│  (Syntax + Safety)      │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  Save to Database       │
│  (Strategy Record)      │
└────────────┬────────────┘
             │
    ┌────────┴────────┐
    ▼                 ▼
┌────────┐      ┌──────────┐
│Execute │      │ Deploy   │
│(Test)  │      │ (Railway)│
└────────┘      └──────────┘
```

## Deployment to Railway

1. User generates strategy code via chat
2. Code is saved in database
3. User clicks "Backtest" or "Deploy"
4. Worker picks up the strategy
5. Runs on Railway cloud (not user device)

## Future Enhancements

- [ ] Live trading with generated code
- [ ] Code optimization suggestions
- [ ] Risk metrics calculation
- [ ] Multi-timeframe strategies
- [ ] Options strategies
- [ ] Portfolio backtesting
- [ ] ML-based indicator generation
- [ ] Strategy composability (combine multiple strategies)

## Testing

### Test via API
```bash
curl -X POST http://localhost:8000/api/strategies/generate-code \
  -H "Content-Type: application/json" \
  -d '{
    "english": "Buy RSI below 30, sell above 70",
    "name": "RSI Test"
  }'
```

### Test via Chat UI
1. Open http://localhost:3000/chat
2. Click "🐍 Full Code" mode
3. Enter strategy description
4. View generated code
5. Click "📋 Copy" to copy code
6. Click "📊 Backtest" to run it

## Files Modified

- `backend/app/ai/code_generator.py` - Full Python code generation
- `backend/app/services/code_executor.py` - Safe code execution
- `backend/app/api/routes.py` - New endpoints
- `frontend/src/components/Chat.tsx` - Enhanced chat UI with code display
- `frontend/src/app/chat/page.tsx` - Chat page
- `frontend/src/app/chat/layout.tsx` - Chat layout (full-screen)

## Troubleshooting

### Issue: "Could not generate code"
- Check GEMINI_API_KEY is set
- Ensure strategy description is clear and includes:
  - Indicators (RSI, MACD, SMA, etc.)
  - Entry conditions
  - Exit conditions

### Issue: "Execution timeout"
- Generated code took >30s to run
- Simplify strategy or reduce data size
- Check for infinite loops

### Issue: "Syntax error in generated code"
- This is logged - review logs via API
- Try rephrasing strategy description
- Fallback to template mode

---

**Ready to build AI-powered trading strategies? Start chatting!** 🚀
