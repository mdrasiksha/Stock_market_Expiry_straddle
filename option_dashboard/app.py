"""Streamlit entrypoint for the Option Dashboard."""
from __future__ import annotations

import base64
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from calculations import holding_time_label, holding_minutes
from config import settings
from journal import TradeJournal
from kite_api import KiteAPI, ShortStraddle
from monitor import TradeMonitor
from sound_assets import ensure_alert_sounds

st.set_page_config(page_title="Option Dashboard", page_icon="📈", layout="wide")
ensure_alert_sounds(settings.success_sound, settings.alarm_sound)


def sound_html(path: Path, loop: bool = False) -> str:
    """Return HTML audio tag for a local WAV file."""
    if not path.exists():
        return ""
    data = base64.b64encode(path.read_bytes()).decode("utf-8")
    loop_attr = " loop" if loop else ""
    return f'<audio autoplay{loop_attr}><source src="data:audio/wav;base64,{data}" type="audio/wav"></audio>'


@st.cache_resource(show_spinner=False)
def kite_client() -> KiteAPI:
    """Cache Kite client for the Streamlit session."""
    return KiteAPI(settings)


def get_monitor(trade: ShortStraddle) -> TradeMonitor:
    """Create or reuse a monitor for the detected active trade."""
    key = f"{trade.underlying}-{trade.expiry}-{trade.strike}-{trade.entry_premium}"
    if st.session_state.get("trade_key") != key:
        st.session_state.trade_key = key
        st.session_state.monitor = TradeMonitor(trade)
    return st.session_state.monitor


def gauge(value: float, title: str, maximum: float = 100) -> go.Figure:
    """Build a compact Plotly gauge."""
    fig = go.Figure(go.Indicator(mode="gauge+number", value=value, title={"text": title}, gauge={"axis": {"range": [None, maximum]}, "bar": {"color": "#00b894"}}))
    fig.update_layout(height=260, margin=dict(l=20, r=20, t=50, b=20))
    return fig


def render_notifications(monitor: TradeMonitor, snapshot) -> None:
    """Render target and stop-loss notifications with sounds."""
    for target in monitor.new_target_alerts(snapshot):
        if target == 70:
            st.markdown("<h1 style='color:gold;text-align:center;'>BOOK PROFIT</h1>", unsafe_allow_html=True)
        else:
            st.success(f"{target}% target reached")
        st.markdown(sound_html(settings.success_sound), unsafe_allow_html=True)
    if monitor.should_alarm(snapshot):
        st.markdown("<h1 style='color:red;text-align:center;'>EXIT NOW</h1>", unsafe_allow_html=True)
        st.markdown(sound_html(settings.alarm_sound, loop=True), unsafe_allow_html=True)
        if st.button("Dismiss Stop Loss Alarm"):
            monitor.alert_state.alarm_dismissed = True


def main() -> None:
    """Render the dashboard."""
    st.title("OPTION DASHBOARD")
    kite = kite_client()
    with st.sidebar:
        st.header("Broker Status")
        configured = settings.is_configured
        logged_in = kite.is_logged_in() if configured else False
        st.metric("Login Status", "Connected" if logged_in else "Not Connected")
        st.metric("Broker", "Zerodha Kite")
        refresh = st.number_input("Refresh Interval", min_value=1, max_value=60, value=settings.refresh_interval)
        st.selectbox("Theme", ["Dark", "Light"], index=0)
        if not configured:
            st.warning("Configure API_KEY and ACCESS_TOKEN in .env")
        if st.button("Save Manual Exit to Journal") and st.session_state.get("last_snapshot") and st.session_state.get("active_trade"):
            trade = st.session_state.active_trade
            snap = st.session_state.last_snapshot
            TradeJournal().append_trade({"Date": datetime.now().date(), "Underlying": trade.underlying, "Expiry": trade.expiry, "Strike": trade.strike, "Entry Premium": trade.entry_premium, "Exit Premium": snap.combined, "Entry Time": trade.entry_time, "Exit Time": datetime.now(), "Holding Minutes": holding_minutes(trade.entry_time), "Profit": snap.profit, "Profit %": snap.profit_pct, "Reason": "Manual Exit", "Manual Exit": True})
            st.success("Trade journaled")
    st_autorefresh(interval=int(refresh) * 1000, key="dashboard_refresh")
    trade = kite.detect_short_straddle()
    if not trade:
        st.info("No active short straddle detected in open Zerodha positions.")
        return
    st.session_state.active_trade = trade
    monitor = get_monitor(trade)
    symbols = [f"{trade.ce_leg.exchange}:{trade.ce_leg.trading_symbol}", f"{trade.pe_leg.exchange}:{trade.pe_leg.trading_symbol}"]
    prices = kite.fetch_live_prices(symbols)
    ce_price = prices.get(symbols[0], trade.ce_leg.average_price)
    pe_price = prices.get(symbols[1], trade.pe_leg.average_price)
    snapshot = monitor.snapshot(ce_price, pe_price)
    st.session_state.last_snapshot = snapshot
    render_notifications(monitor, snapshot)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Current Strategy", "0 DTE Short Straddle")
    c2.metric("Underlying", trade.underlying)
    c3.metric("Expiry", trade.expiry)
    c4.metric("Strike", trade.strike)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Entry Premium", trade.entry_premium)
    c2.metric("Current Combined Premium", snapshot.combined)
    c3.metric("Current MTM", snapshot.profit)
    c4.metric("Status", snapshot.status)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Entry Time", trade.entry_time.strftime("%H:%M:%S"))
    c2.metric("Current Profit %", f"{snapshot.profit_pct}%")
    c3.metric("Current ROI", f"{snapshot.roi_pct}%")
    c4.metric("Holding Time", holding_time_label(trade.entry_time))
    st.progress(min(max(snapshot.decay_pct / 100, 0), 1), text=f"Premium Decay Meter: {snapshot.decay_pct}%")
    g1, g2 = st.columns(2)
    g1.plotly_chart(gauge(snapshot.profit_pct, "Profit Gauge"), use_container_width=True)
    g2.plotly_chart(gauge(snapshot.decay_pct, "Premium Decay"), use_container_width=True)
    st.subheader("Profit Targets")
    st.dataframe(pd.DataFrame(snapshot.target_rows), use_container_width=True, hide_index=True)
    st.subheader("Stop Loss")
    st.dataframe(pd.DataFrame(snapshot.sl_rows), use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
