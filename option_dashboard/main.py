"""Main Streamlit entrypoint for the AI-powered 0DTE Trading System."""
from __future__ import annotations

import streamlit as st
from streamlit_autorefresh import st_autorefresh

from config import settings
from dashboard import apply_theme, render_ai_assistant, render_analytics, render_checklist, render_exit_engine, render_greeks, render_live_monitor, render_quality, render_risk_gate, render_strategy
from kite_api import KiteAPI
from market import demo_snapshot
from risk import RiskEngine
from sound_assets import ensure_alert_sounds
from strategy import MarketRegimeDetector, StrategyEngine

st.set_page_config(page_title="0DTE Short Straddle Monitor", page_icon="⚡", layout="wide")


def main() -> None:
    """Render the complete AI-powered trading workflow."""
    ensure_alert_sounds(settings.success_sound, settings.alarm_sound)
    apply_theme()
    st.title("⚡ AI Powered 0DTE Short Straddle Monitor")
    with st.sidebar:
        st.header("Settings")
        capital = st.number_input("Capital", value=float(settings.capital), step=10000.0)
        risk_pct = st.number_input("Risk %", value=float(settings.risk_percent), step=0.25)
        st.number_input("SL %", value=float(settings.sl_percent), step=5.0)
        st.number_input("Target %", value=float(settings.target_percent), step=5.0)
        auto_exit = st.toggle("Auto Exit", value=settings.auto_exit)
        auto_refresh = st.toggle("Auto Refresh", value=settings.auto_refresh)
        st.selectbox("Theme", ["Dark", "Light"], index=0)
        st.selectbox("Broker", ["Dummy", "Zerodha", "Dhan", "Fyers", "Angel"], index=0)
        st.toggle("Paper Trading", value=settings.paper_trading)
        refresh = st.number_input("Refresh Interval", min_value=1, max_value=60, value=settings.refresh_interval)
        kite = KiteAPI(settings)
        st.metric("Zerodha", "Connected" if kite.is_logged_in() else "Demo/Paper")
        st.caption(f"Auto Exit {'ON' if auto_exit else 'OFF'} • Auto Refresh {'ON' if auto_refresh else 'OFF'} • Risk {risk_pct}% on ₹{capital:,.0f}")
    if auto_refresh:
        st_autorefresh(interval=int(refresh) * 1000, key="ai_dashboard_refresh")

    market = demo_snapshot()
    risk_engine = RiskEngine(settings)
    decision = risk_engine.no_trade_decision(market)
    render_risk_gate(decision)
    checklist = risk_engine.checklist(market)
    quality = risk_engine.quality_score(market)
    render_checklist(checklist)
    render_quality(quality)

    regime = MarketRegimeDetector().detect(market)
    recommendation = StrategyEngine().recommend(market, regime)
    render_strategy(regime, recommendation)
    render_ai_assistant(market, quality, recommendation, regime)
    combined = recommendation.strike_selection.expected_premium
    risk_plan = risk_engine.risk_plan(combined, pop=recommendation.strike_selection.expected_pop / 100)
    st.subheader("Risk Engine")
    st.dataframe({"Metric": list(risk_plan.__dict__.keys()), "Value": [str(v) for v in risk_plan.__dict__.values()]}, use_container_width=True)
    render_greeks(market)
    render_live_monitor(market, combined=max(combined * 0.92, 0), entry=combined, pnl=(combined - combined * 0.92) * 50)
    render_exit_engine(market, combined=max(combined * 0.92, 0), entry=combined)
    render_analytics()


if __name__ == "__main__":
    main()
