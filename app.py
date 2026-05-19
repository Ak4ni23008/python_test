import streamlit as st
import subprocess
import sys
import os
import tempfile
import pandas as pd
import plotly.express as px

# =========================================================
# IMPORT YOUR BACKTEST FILE
# =========================================================

from backtest_20min import backtest, BacktestConfig

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Professional Algo Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown("""
<style>

.stApp {
    background-color: #0f172a;
    color: white;
}

section[data-testid="stSidebar"] {
    background-color: #111827;
}

.block-container {
    padding-top: 1rem;
}

[data-testid="metric-container"] {
    background: linear-gradient(135deg,#1e293b,#111827);
    border: 1px solid #334155;
    padding: 20px;
    border-radius: 18px;
    box-shadow: 0px 4px 20px rgba(0,0,0,0.4);
}

h1, h2, h3 {
    color: white !important;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# AUTO CREATE DEMO CSV
# =========================================================

demo_csv = "yesbank_5m.csv"

if not os.path.exists(demo_csv):

    demo_data = pd.DataFrame({
        "date": pd.date_range(
            start="2025-01-01 09:15:00",
            periods=5000,
            freq="5min"
        ),
        "open": [20 + i * 0.03 for i in range(5000)],
        "high": [20.2 + i * 0.03 for i in range(5000)],
        "low": [19.8 + i * 0.03 for i in range(5000)],
        "close": [20.1 + i * 0.03 for i in range(5000)],
        "volume": [10000 + i * 20 for i in range(5000)],
    })

    demo_data.to_csv(demo_csv, index=False)

# =========================================================
# HEADER
# =========================================================

st.title("📈 Professional Algo Trading Dashboard")
st.caption("Backtesting + Live Trading + Analytics")

# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("⚙ Dashboard")

module = st.sidebar.radio(
    "Select Module",
    [
        "📊 Backtesting",
        "🚀 Live Trading"
    ]
)

# =========================================================
# BACKTESTING PAGE
# =========================================================

if module == "📊 Backtesting":

    st.header("📊 Backtesting Engine")

    st.markdown("---")

    # =====================================================
    # INPUTS
    # =====================================================

    uploaded_csv = st.file_uploader(
        "Upload OHLC CSV (required on Railway — your laptop paths won't work in the cloud)",
        type=["csv"],
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        if uploaded_csv is not None:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
            tmp.write(uploaded_csv.getbuffer())
            tmp.close()
            csv_path = tmp.name
            st.caption(f"Using uploaded file: {uploaded_csv.name}")
        else:
            csv_path = st.text_input(
                "CSV Path (local only)",
                value=demo_csv,
            )

    with col2:
        entry_mode = st.selectbox(
            "Entry Mode",
            [
                "buy_0915_sell_0935",
                "first_bar_each_day",
                "every_bar"
            ]
        )

    with col3:
        quantity = st.number_input(
            "Quantity",
            value=1
        )

    col4, col5, col6 = st.columns(3)

    with col4:
        brokerage = st.number_input(
            "Brokerage",
            value=20.0
        )

    with col5:
        slippage = st.slider(
            "Slippage (bps)",
            0,
            100,
            5
        )

    with col6:
        hold_minutes = st.number_input(
            "Hold Minutes",
            value=20
        )

    run_backtest = st.button("▶ RUN BACKTEST")

    # =====================================================
    # RUN BACKTEST
    # =====================================================

    if run_backtest:

        try:

            cfg = BacktestConfig(
                csv_path=csv_path,
                entry_mode=entry_mode,
                quantity=quantity,
                brokerage_per_trade=brokerage,
                slippage_bps=slippage,
                hold_minutes=hold_minutes,
            )

            trades, stats = backtest(cfg)

            st.success("✅ Backtest Completed Successfully")

            # =================================================
            # METRICS
            # =================================================

            st.subheader("📈 Strategy Metrics")

            m1, m2, m3, m4, m5 = st.columns(5)

            m1.metric(
                "💰 Total PnL",
                f"₹{stats['total_net_pnl']:.2f}"
            )

            m2.metric(
                "🎯 Win Rate",
                f"{stats['win_rate_pct']:.2f}%"
            )

            m3.metric(
                "📉 Max Drawdown",
                f"₹{stats['max_drawdown']:.2f}"
            )

            m4.metric(
                "📈 Best Trade",
                f"₹{stats['best_trade']:.2f}"
            )

            m5.metric(
                "📊 Total Trades",
                stats['trades']
            )

            st.markdown("---")

            # =================================================
            # EQUITY CURVE
            # =================================================

            st.subheader("📈 Equity Curve")

            trades["equity_curve"] = trades["net_pnl"].cumsum()

            fig_equity = px.line(
                trades,
                y="equity_curve",
                title="Equity Curve"
            )

            fig_equity.update_layout(
                template="plotly_dark",
                paper_bgcolor="#0f172a",
                plot_bgcolor="#0f172a",
                height=500
            )

            st.plotly_chart(
                fig_equity,
                use_container_width=True
            )

            # =================================================
            # PNL DISTRIBUTION
            # =================================================

            st.subheader("📉 PnL Distribution")

            fig_hist = px.histogram(
                trades,
                x="net_pnl",
                nbins=50,
                title="Trade Distribution"
            )

            fig_hist.update_layout(
                template="plotly_dark",
                paper_bgcolor="#0f172a",
                plot_bgcolor="#0f172a",
                height=500
            )

            st.plotly_chart(
                fig_hist,
                use_container_width=True
            )

            # =================================================
            # TRADES TABLE
            # =================================================

            st.subheader("📋 Trades")

            st.dataframe(
                trades,
                use_container_width=True,
                height=500
            )

            # =================================================
            # DOWNLOAD CSV
            # =================================================

            csv_download = trades.to_csv(index=False)

            st.download_button(
                label="⬇ Download Trades CSV",
                data=csv_download,
                file_name="trades.csv",
                mime="text/csv"
            )

        except Exception as e:
            st.error(f"Backtest Error: {e}")

# =========================================================
# LIVE TRADING PAGE
# =========================================================

elif module == "🚀 Live Trading":

    st.header("🚀 Live Trading Engine")

    st.markdown("---")

    st.info(
        "On **Railway/cloud**, use a scheduled cron job to run `live_trade_0920_0921.py` "
        "(see RAILWAY.md). The button below is for local use and may time out on cloud hosts."
    )

    st.warning("⚠ Always use Dry Run before Real Trading")

    # =====================================================
    # SETTINGS
    # =====================================================

    col1, col2 = st.columns(2)

    with col1:

        qty = st.number_input(
            "Quantity",
            value=1
        )

        buy_time = st.text_input(
            "Buy Time (HH:MM)",
            value="11:55"
        )

        sell_time = st.text_input(
            "Sell Time (HH:MM)",
            value="11:56"
        )

    with col2:

        dry_run = st.checkbox(
            "Dry Run",
            value=True
        )

        disable_ssl = st.checkbox(
            "Disable SSL Verify"
        )

    # =====================================================
    # START BUTTON
    # =====================================================

    start_live = st.button("▶ START LIVE TRADING")

    # =====================================================
    # RUN LIVE TRADING FILE
    # =====================================================

    if start_live:

        st.success("🚀 Starting Live Trading")

        cmd = [
            sys.executable,
            "live_trade_0920_0921.py",
            "--qty",
            str(qty),
            "--buy",
            buy_time,
            "--sell",
            sell_time
        ]

        if dry_run:
            cmd.append("--dry-run")

        if disable_ssl:
            cmd.append("--disable-ssl-verify")

        st.subheader("📜 Live Logs")

        log_box = st.empty()

        try:

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            logs = ""

            while True:

                line = process.stdout.readline()

                if not line and process.poll() is not None:
                    break

                if line:
                    logs += line
                    log_box.code(logs)

            process.wait()

            if process.returncode == 0:
                st.success("✅ Live Trading Completed Successfully")
            else:
                st.error("❌ Live Trading Failed")

        except Exception as e:
            st.error(f"Execution Error: {e}")