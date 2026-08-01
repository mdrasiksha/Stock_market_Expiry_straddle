"""Streamlit UI for the AI-powered 0DTE trading system."""
from __future__ import annotations

import base64
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from analytics import analytics_report, run_backtest
from config import settings
from greeks import greeks_frame
from market import MarketSnapshot
from risk import ChecklistItem, RiskDecision, RiskEngine, TradeQuality
from signals import exit_signal
from strategy import RegimeResult, StrategyRecommendation


def sound_html(path: Path, loop: bool = False) -> str:
    """Return HTML audio tag for a local WAV file."""
    if not path.exists():
        return ""
    data = base64.b64encode(path.read_bytes()).decode("utf-8")
    loop_attr = " loop" if loop else ""
    return f'<audio autoplay{loop_attr}><source src="data:audio/wav;base64,{data}" type="audio/wav"></audio>'


def apply_theme() -> None:
    """Apply a dark TradingView-inspired visual style."""
    st.markdown("""
    <style>
    .stApp {background: #080d14; color: #e8eef7;}
    [data-testid="stMetric"] {background: linear-gradient(135deg,#111827,#0f172a); border: 1px solid #243247; border-radius: 18px; padding: 16px; box-shadow: 0 0 22px rgba(0,184,148,.12);} 
    .risk-card {border-radius:18px; padding:18px; background:#111827; border:1px solid #2b3648;}
    .no-trade {font-size:42px; color:#ff4757; font-weight:800; text-align:center;}
    .trade-ok {font-size:36px; color:#00d084; font-weight:800; text-align:center;}
    </style>
    """, unsafe_allow_html=True)


def gauge(value: float, title: str, maximum: float = 100, color: str = "#00b894") -> go.Figure:
    """Build a compact gauge chart."""
    fig = go.Figure(go.Indicator(mode="gauge+number", value=value, title={"text": title}, gauge={"axis": {"range": [0, maximum]}, "bar": {"color": color}}))
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20), paper_bgcolor="#080d14", font_color="#e8eef7")
    return fig


def render_risk_gate(decision: RiskDecision) -> None:
    """Render the mandatory no-trade gate before strategy details."""
    css = "trade-ok" if decision.should_trade else "no-trade"
    st.markdown(f'<div class="{css}">{decision.title}</div>', unsafe_allow_html=True)
    rows = [{"Check": c.name, "Status": "❌ Failed" if c.failed else "✅ Passed", "Detail": c.detail} for c in decision.checks]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def render_checklist(items: list[ChecklistItem]) -> None:
    """Render pre-trade checklist with pass count."""
    passed = sum(item.passed for item in items)
    st.subheader(f"Pre Trade Checklist — Passed {passed}/{len(items)}")
    st.dataframe(pd.DataFrame([{"Item": item.name, "Status": "✅" if item.passed else "❌", "Detail": item.detail} for item in items]), use_container_width=True, hide_index=True)


def render_quality(quality: TradeQuality) -> None:
    """Render trade score and weighted component heat map."""
    c1, c2 = st.columns([1, 2])
    c1.plotly_chart(gauge(quality.score, "Trade Quality Score", color="#00d084" if quality.score >= 75 else "#ff4757"), use_container_width=True)
    c1.metric("Recommendation", f"{quality.stars} {quality.label}")
    comp = pd.DataFrame([{"Component": key, "Score": value} for key, value in quality.components.items()])
    c2.plotly_chart(px.bar(comp, x="Component", y="Score", title="Weighted Score Components", color="Score", color_continuous_scale="Viridis"), use_container_width=True)


def render_strategy(regime: RegimeResult, recommendation: StrategyRecommendation) -> None:
    """Render regime and strategy cards."""
    st.subheader("Market Regime Detection")
    c1, c2, c3 = st.columns(3)
    c1.metric("Regime", regime.regime)
    c2.metric("Confidence", f"{regime.confidence:.0f}%")
    c3.metric("Auto Strategy", recommendation.name)
    st.caption(" • ".join(regime.reasons + [recommendation.rationale]))
    strike = recommendation.strike_selection
    st.dataframe(pd.DataFrame([strike.__dict__]), use_container_width=True, hide_index=True)


def render_live_monitor(market: MarketSnapshot, combined: float, entry: float, pnl: float) -> None:
    """Render professional position dashboard cards."""
    st.subheader("Live Position Monitor")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Large P&L", f"₹{pnl:,.2f}", delta_color="normal")
    c2.metric("Combined Premium", f"₹{entry:.2f}")
    c3.metric("Current Premium", f"₹{combined:.2f}")
    c4.metric("Current IV", f"{market.option_iv:.2f}%")
    c1, c2, c3 = st.columns(3)
    c1.plotly_chart(gauge(max(0, 100 - market.vwap_distance_pct * 100), "Risk Meter"), use_container_width=True)
    c2.plotly_chart(gauge(min(100, market.adx * 3), "Trend Meter", color="#fdcb6e"), use_container_width=True)
    heat = pd.DataFrame({"Metric": ["Theta", "IV", "VIX", "VWAP", "Breadth"], "Value": [70, market.option_iv, market.india_vix, 100 - market.vwap_distance_pct * 100, market.market_breadth * 100]})
    c3.plotly_chart(px.imshow([heat["Value"].tolist()], x=heat["Metric"], color_continuous_scale="RdYlGn", title="Heat Map"), use_container_width=True)


def render_ai_assistant(market: MarketSnapshot, quality: TradeQuality, strategy: StrategyRecommendation, regime: RegimeResult) -> None:
    """Generate natural-language AI-style trade analysis."""
    st.subheader("AI Trade Assistant")
    st.info(f"Today's Analysis\n\nMarket is classified as {regime.regime}. Price is {market.vwap_distance_pct:.2f}% from VWAP and VWAP slope is {market.vwap_slope:.3f}. IV is {'stable' if abs(market.option_iv_change_pct) <= 3 else 'unstable'} and premium decay has {'started' if market.premium_decay_started else 'not started'}. Trade Score {quality.score:.0f}. Recommended Strategy: {strategy.name}. Confidence: {strategy.confidence:.0f}%.")


def render_analytics() -> None:
    """Render journal analytics and backtest panels."""
    st.subheader("Analytics")
    report = analytics_report(settings.journal_path)
    if report.metrics:
        cols = st.columns(4)
        for idx, (key, value) in enumerate(report.metrics.items()):
            cols[idx % 4].metric(key, value)
        st.dataframe(report.monthly, use_container_width=True, hide_index=True)
        st.dataframe(report.yearly, use_container_width=True, hide_index=True)
    else:
        st.caption("No completed trades in journal yet.")
    days = st.selectbox("Backtest Window", [30, 90, 180, 365], index=1)
    st.dataframe(pd.DataFrame([run_backtest(days, settings.capital)]), use_container_width=True, hide_index=True)


def render_greeks(market: MarketSnapshot) -> None:
    """Render Greeks panel."""
    st.subheader("Option Greeks Panel")
    st.dataframe(greeks_frame(market), use_container_width=True, hide_index=True)


def render_exit_engine(market: MarketSnapshot, combined: float, entry: float) -> None:
    """Render exit engine output."""
    signal = exit_signal(market, combined, entry, settings.target_percent, settings.sl_percent)
    st.subheader("Exit Engine")
    st.metric("Exit Status", "EXIT NOW" if signal.should_exit else "HOLD")
    st.write("Exit Reason:", ", ".join(signal.reasons) if signal.reasons else "None")
