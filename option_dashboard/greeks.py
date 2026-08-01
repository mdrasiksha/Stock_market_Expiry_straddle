"""Option Greeks table builders."""
from __future__ import annotations

import pandas as pd

from market import MarketSnapshot


def greeks_frame(market: MarketSnapshot) -> pd.DataFrame:
    """Return option-chain Greeks with IV rank and percentile columns."""
    rows = [{"Strike": q.strike, "Type": q.option_type, "Delta": q.delta, "Gamma": q.gamma, "Theta": q.theta, "Vega": q.vega, "IV": q.iv, "IV Rank": market.iv_rank, "IV Percentile": market.iv_percentile, "Bid": q.bid, "Ask": q.ask, "OI": q.oi, "Volume": q.volume} for q in market.option_chain]
    return pd.DataFrame(rows)
