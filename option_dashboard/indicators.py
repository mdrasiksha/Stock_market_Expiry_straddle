"""Technical indicator helpers used by regime and risk engines."""
from __future__ import annotations

import numpy as np
import pandas as pd


def ema(series: pd.Series, span: int) -> pd.Series:
    """Return exponential moving average."""
    return series.ewm(span=span, adjust=False).mean()


def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Return Average True Range."""
    ranges = pd.concat([(high - low), (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1)
    return ranges.max(axis=1).rolling(period).mean()


def adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Return Average Directional Index."""
    plus_dm = high.diff().clip(lower=0)
    minus_dm = (-low.diff()).clip(lower=0)
    tr = atr(high, low, close, 1).replace(0, np.nan)
    plus_di = 100 * plus_dm.rolling(period).mean() / tr.rolling(period).mean()
    minus_di = 100 * minus_dm.rolling(period).mean() / tr.rolling(period).mean()
    dx = (abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, np.nan)) * 100
    return dx.rolling(period).mean().fillna(0)


def vwap(price: pd.Series, volume: pd.Series) -> pd.Series:
    """Return volume-weighted average price."""
    return (price * volume).cumsum() / volume.cumsum().replace(0, np.nan)
