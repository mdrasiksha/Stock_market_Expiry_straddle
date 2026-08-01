"""Trade journal analytics and simple historical backtesting."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class AnalyticsReport:
    """Performance analytics summary."""

    metrics: dict[str, float | str]
    monthly: pd.DataFrame
    yearly: pd.DataFrame


def load_trades(path: Path) -> pd.DataFrame:
    """Load journal CSV with robust empty-file handling."""
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    return pd.read_csv(path)


def analytics_report(path: Path) -> AnalyticsReport:
    """Calculate win rate, expectancy, Sharpe, drawdown, profit factor, and best timing stats."""
    df = load_trades(path)
    if df.empty or "Profit" not in df:
        return AnalyticsReport({}, pd.DataFrame(), pd.DataFrame())
    pnl = pd.to_numeric(df["Profit"], errors="coerce").fillna(0)
    wins = pnl[pnl > 0]
    losses = pnl[pnl < 0]
    equity = pnl.cumsum()
    drawdown = equity - equity.cummax()
    metrics = {
        "Win Rate": round(len(wins) / len(pnl) * 100, 2) if len(pnl) else 0,
        "Average Profit": round(wins.mean() if len(wins) else 0, 2),
        "Average Loss": round(losses.mean() if len(losses) else 0, 2),
        "Expectancy": round(pnl.mean(), 2),
        "Sharpe Ratio": round((pnl.mean() / pnl.std()) * np.sqrt(252), 2) if pnl.std() else 0,
        "Maximum Drawdown": round(drawdown.min() if len(drawdown) else 0, 2),
        "Profit Factor": round(wins.sum() / abs(losses.sum()), 2) if abs(losses.sum()) else float("inf"),
        "Best Weekday": _best_group(df, pnl, "Date", "%A"),
        "Best Entry Time": _best_column(df, pnl, "Entry Time"),
        "Best Exit Time": _best_column(df, pnl, "Exit Time"),
        "Best Premium": _best_column(df, pnl, "Entry Premium"),
    }
    dated = df.assign(Date=pd.to_datetime(df.get("Date"), errors="coerce"), Profit=pnl).dropna(subset=["Date"])
    monthly = dated.groupby(dated["Date"].dt.to_period("M"))["Profit"].sum().reset_index().astype(str)
    yearly = dated.groupby(dated["Date"].dt.year)["Profit"].sum().reset_index().astype(str)
    return AnalyticsReport(metrics, monthly, yearly)


def run_backtest(days: int, capital: float = 500000) -> dict[str, float]:
    """Deterministic placeholder backtest for 30/90/180/365 day research windows."""
    rng = np.random.default_rng(days)
    returns = rng.normal(0.0012, 0.006, days)
    equity = capital * (1 + pd.Series(returns)).cumprod()
    pnl = equity.diff().fillna(equity.iloc[0] - capital)
    wins, losses = pnl[pnl > 0], pnl[pnl < 0]
    cagr = ((equity.iloc[-1] / capital) ** (365 / days) - 1) * 100
    dd = (equity - equity.cummax()).min()
    return {"CAGR": round(cagr, 2), "Win Rate": round(len(wins) / days * 100, 2), "Drawdown": round(float(dd), 2), "Profit Factor": round(float(wins.sum() / abs(losses.sum())), 2) if abs(losses.sum()) else float("inf")}


def _best_group(df: pd.DataFrame, pnl: pd.Series, date_col: str, fmt: str) -> str:
    dates = pd.to_datetime(df.get(date_col), errors="coerce")
    grouped = pnl.groupby(dates.dt.strftime(fmt)).mean()
    return str(grouped.idxmax()) if not grouped.empty else "N/A"


def _best_column(df: pd.DataFrame, pnl: pd.Series, column: str) -> str:
    if column not in df:
        return "N/A"
    grouped = pnl.groupby(df[column]).mean()
    return str(grouped.idxmax()) if not grouped.empty else "N/A"
