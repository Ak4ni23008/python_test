# Example live trade script — edit and run from Live Trading → Write Code tab
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from live_trade_0920_0921 import LiveConfig, run_once

IST = ZoneInfo("Asia/Kolkata")
now = datetime.now(tz=IST)

cfg = LiveConfig(
    security_id="11915",  # Yes Bank
    quantity=1,
    buy_time=(now + timedelta(seconds=2)).time(),
    sell_time=(now + timedelta(seconds=5)).time(),
    dry_run=True,  # set False only when ready for real orders
)

exit_code = run_once(cfg)
print(f"\nExit code: {exit_code}")
