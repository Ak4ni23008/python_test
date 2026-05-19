from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

import argparse
import os
import time
from dataclasses import dataclass
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from dhanhq import dhanhq

# =========================================================
# TIMEZONE
# =========================================================

IST = ZoneInfo("Asia/Kolkata")

# =========================================================
# YES BANK SECURITY ID
# =========================================================

YES_BANK_SECURITY_ID = "11915"

# =========================================================
# CONFIG
# =========================================================

@dataclass(frozen=True)
class LiveConfig:

    security_id: str
    quantity: int

    exchange_segment: str = "NSE_EQ"
    product_type: str = "INTRADAY"
    order_type: str = "MARKET"

    buy_time: dtime = dtime(11, 55)
    sell_time: dtime = dtime(11, 56)

    poll_seconds: float = 0.5

    dry_run: bool = False


# =========================================================
# HELPERS
# =========================================================

def _parse_hhmm(s: str) -> dtime:

    try:
        hh, mm = s.strip().split(":")
        return dtime(int(hh), int(mm))

    except Exception as e:
        raise argparse.ArgumentTypeError(
            "Time must be HH:MM"
        ) from e


def _now_ist() -> datetime:
    return datetime.now(tz=IST)


def _is_weekday(dt: datetime) -> bool:
    return dt.weekday() < 5


def _wait_until(target_dt: datetime, poll_seconds: float) -> None:

    while True:

        now = _now_ist()

        if now >= target_dt:
            return

        sleep_for = min(
            poll_seconds,
            max(0.05, (target_dt - now).total_seconds())
        )

        time.sleep(sleep_for)


# =========================================================
# ORDER STATUS
# =========================================================

def _order_failed(resp: object) -> bool:

    if not isinstance(resp, dict):
        return True

    if resp.get("dry_run"):
        return False

    return str(resp.get("status", "")).lower() == "failure"


# =========================================================
# PLACE ORDER
# =========================================================

def _place_market_order(
    dhan: dhanhq | None,
    *,
    security_id: str,
    exchange_segment: str,
    transaction_type: str,
    quantity: int,
    order_type: str,
    product_type: str,
    dry_run: bool,
) -> dict:

    # =====================================================
    # DRY RUN
    # =====================================================

    if dry_run:

        return {
            "dry_run": True,
            "security_id": security_id,
            "transaction_type": transaction_type,
            "quantity": quantity,
            "time": _now_ist().isoformat(),
        }

    # =====================================================
    # REAL ORDER
    # =====================================================

    if dhan is None:
        raise RuntimeError("Dhan client not initialized")

    response = dhan.place_order(
        security_id=security_id,
        exchange_segment=exchange_segment,
        transaction_type=transaction_type,
        quantity=quantity,
        order_type=order_type,
        product_type=product_type,
        price=0
    )

    return response


# =========================================================
# MAIN LIVE LOGIC
# =========================================================

def run_once(cfg: LiveConfig) -> int:

    dhan = None

    # =====================================================
    # CONNECT DHAN
    # =====================================================

    if not cfg.dry_run:

        load_dotenv()

        client_id = os.getenv("DHAN_CLIENT_ID", "").strip()
        access_token = os.getenv("DHAN_ACCESS_TOKEN", "").strip()

        if not client_id or not access_token:

            raise RuntimeError(
                "Missing DHAN_CLIENT_ID or DHAN_ACCESS_TOKEN in .env"
            )

        dhan = dhanhq(
            client_id=client_id,
            access_token=access_token
        )

        print("Connected To Dhan", flush=True)

    # =====================================================
    # CHECK MARKET DAY
    # =====================================================

    now = _now_ist()

    if not _is_weekday(now):

        print("Weekend - Market Closed")
        return 0

    # =====================================================
    # CREATE BUY/SELL TIMES
    # =====================================================

    today = now.date()

    buy_dt = datetime.combine(
        today,
        cfg.buy_time,
        tzinfo=IST
    )

    sell_dt = datetime.combine(
        today,
        cfg.sell_time,
        tzinfo=IST
    )

    if sell_dt <= buy_dt:
        raise ValueError("Sell time must be after buy time")

    # =====================================================
    # WAIT FOR BUY TIME
    # =====================================================

    if now < buy_dt:

        print(
            f"Waiting For BUY Time {buy_dt.strftime('%H:%M:%S')} IST"
        )

        _wait_until(
            buy_dt,
            cfg.poll_seconds
        )

    # =====================================================
    # BUY ORDER
    # =====================================================

    print("\nPLACING BUY ORDER")

    buy_resp = _place_market_order(
        dhan,
        security_id=cfg.security_id,
        exchange_segment=cfg.exchange_segment,
        transaction_type="BUY",
        quantity=cfg.quantity,
        order_type=cfg.order_type,
        product_type=cfg.product_type,
        dry_run=cfg.dry_run,
    )

    print("BUY RESPONSE:", buy_resp)

    if _order_failed(buy_resp):

        print("BUY FAILED")
        return 1

    print("BUY SUCCESSFUL")

    # =====================================================
    # WAIT FOR SELL TIME
    # =====================================================

    now = _now_ist()

    if now < sell_dt:

        print(
            f"\nWaiting For SELL Time {sell_dt.strftime('%H:%M:%S')} IST"
        )

        _wait_until(
            sell_dt,
            cfg.poll_seconds
        )

    # =====================================================
    # SELL ORDER
    # =====================================================

    print("\nPLACING SELL ORDER")

    sell_resp = _place_market_order(
        dhan,
        security_id=cfg.security_id,
        exchange_segment=cfg.exchange_segment,
        transaction_type="SELL",
        quantity=cfg.quantity,
        order_type=cfg.order_type,
        product_type=cfg.product_type,
        dry_run=cfg.dry_run,
    )

    print("SELL RESPONSE:", sell_resp)

    if _order_failed(sell_resp):

        print("SELL FAILED")
        return 1

    print("SELL SUCCESSFUL")

    print("\nSTRATEGY COMPLETED")

    return 0


# =========================================================
# MAIN
# =========================================================

def main() -> int:

    p = argparse.ArgumentParser(
        description="Live Intraday Strategy"
    )

    p.add_argument(
        "--security-id",
        default=YES_BANK_SECURITY_ID
    )

    p.add_argument(
        "--qty",
        type=int,
        default=1
    )

    p.add_argument(
        "--exchange",
        default="NSE_EQ"
    )

    p.add_argument(
        "--product",
        default="INTRADAY"
    )

    p.add_argument(
        "--buy",
        type=_parse_hhmm,
        default=dtime(11, 55)
    )

    p.add_argument(
        "--sell",
        type=_parse_hhmm,
        default=dtime(11, 56)
    )

    p.add_argument(
        "--dry-run",
        action="store_true"
    )

    args = p.parse_args()

    cfg = LiveConfig(
        security_id=str(args.security_id),
        quantity=int(args.qty),
        exchange_segment=str(args.exchange),
        product_type=str(args.product),
        buy_time=args.buy,
        sell_time=args.sell,
        dry_run=bool(args.dry_run),
    )

    return run_once(cfg)


# =========================================================
# START
# =========================================================

if __name__ == "__main__":
    raise SystemExit(main())