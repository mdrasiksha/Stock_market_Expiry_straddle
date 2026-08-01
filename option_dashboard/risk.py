"""Pre-trade no-trade filter, checklist, scoring, and risk calculations."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import time

from config import Settings, settings
from market import MarketSnapshot


@dataclass(frozen=True)
class RiskCheck:
    """Single risk gate result."""

    name: str
    failed: bool
    detail: str


@dataclass(frozen=True)
class RiskDecision:
    """Complete no-trade decision."""

    should_trade: bool
    title: str
    checks: list[RiskCheck]

    @property
    def failed_checks(self) -> list[RiskCheck]:
        """Return failed no-trade checks."""
        return [check for check in self.checks if check.failed]


@dataclass(frozen=True)
class ChecklistItem:
    """Pre-trade checklist result."""

    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class TradeQuality:
    """Weighted trade-quality score."""

    score: float
    stars: str
    label: str
    components: dict[str, float]


@dataclass(frozen=True)
class RiskPlan:
    """Position-level risk plan."""

    capital: float
    margin_required: float
    max_risk: float
    combined_premium: float
    target: float
    expected_return: float
    risk_reward: float
    probability_of_profit: float
    stop_levels: dict[str, float]


class RiskEngine:
    """Institutional pre-trade and position risk engine."""

    def __init__(self, app_settings: Settings = settings) -> None:
        self.settings = app_settings

    def no_trade_decision(self, market: MarketSnapshot) -> RiskDecision:
        """Return NO TRADE when any hard risk condition is true."""
        checks = [
            RiskCheck("RBI Policy", market.rbi_policy, "RBI policy event enabled"),
            RiskCheck("Budget Day", market.budget_day, "Union budget day enabled"),
            RiskCheck("Major Global Event", market.major_global_event, "Major scheduled/unscheduled global event"),
            RiskCheck("India VIX > threshold", market.india_vix > self.settings.vix_threshold, f"{market.india_vix:.2f} > {self.settings.vix_threshold:.2f}"),
            RiskCheck("India VIX Spike >5%", market.india_vix_change_pct > 5, f"{market.india_vix_change_pct:.2f}%"),
            RiskCheck("Gap Up >1%", market.gap_pct > 1, f"{market.gap_pct:.2f}%"),
            RiskCheck("Gap Down >1%", market.gap_pct < -1, f"{market.gap_pct:.2f}%"),
            RiskCheck("Opening Range >0.8%", market.opening_range_pct > 0.8, f"{market.opening_range_pct:.2f}%"),
            RiskCheck("ADX >25", market.adx > 25, f"ADX {market.adx:.2f}"),
            RiskCheck("Price away from VWAP >0.4%", market.vwap_distance_pct > 0.4, f"{market.vwap_distance_pct:.2f}%"),
            RiskCheck("Circuit Day", market.circuit_day, "Circuit filter enabled"),
            RiskCheck("Extreme Option IV", market.iv_rank > 80 or market.iv_percentile > 85, f"IVR {market.iv_rank:.1f}, IVP {market.iv_percentile:.1f}"),
            RiskCheck("Low Liquidity", self._low_liquidity(market), "Wide spreads, low OI, or low volume"),
            RiskCheck("Weekly Monthly Expiry Overlap", market.weekly_monthly_overlap, "Expiry overlap enabled"),
            RiskCheck("Exchange Technical Issue", market.exchange_issue, "Exchange issue enabled"),
        ]
        failed = any(check.failed for check in checks)
        return RiskDecision(not failed, "✅ TRADE ALLOWED" if not failed else "🚫 NO TRADE TODAY", checks)

    def checklist(self, market: MarketSnapshot) -> list[ChecklistItem]:
        """Return the discretionary pre-trade checklist."""
        now = market.timestamp.time()
        return [
            ChecklistItem("Time >9:20", now > time(9, 20), now.strftime("%H:%M")),
            ChecklistItem("Opening Range Complete", market.opening_range_complete, f"Range {market.opening_range_pct:.2f}%"),
            ChecklistItem("Price near VWAP", market.vwap_distance_pct <= 0.4, f"Distance {market.vwap_distance_pct:.2f}%"),
            ChecklistItem("VWAP Flat", abs(market.vwap_slope) <= 0.03, f"Slope {market.vwap_slope:.3f}"),
            ChecklistItem("Premium Decay Started", market.premium_decay_started, "Decay observed"),
            ChecklistItem("IV Stable", abs(market.option_iv_change_pct) <= 3, f"IV change {market.option_iv_change_pct:.2f}%"),
            ChecklistItem("OI Balanced", 0.75 <= market.pcr <= 1.25, f"PCR {market.pcr:.2f}"),
            ChecklistItem("PCR Neutral", 0.8 <= market.pcr <= 1.2, f"PCR {market.pcr:.2f}"),
            ChecklistItem("India VIX Stable", abs(market.india_vix_change_pct) <= 5, f"VIX change {market.india_vix_change_pct:.2f}%"),
            ChecklistItem("No Economic Event", not (market.rbi_policy or market.budget_day or market.major_global_event), "Calendar clean"),
            ChecklistItem("No Existing Position", market.no_existing_position, "Position gate"),
            ChecklistItem("Good Bid Ask Spread", not self._low_liquidity(market), "Spread/OI/volume OK"),
        ]

    def quality_score(self, market: MarketSnapshot) -> TradeQuality:
        """Calculate 0-100 weighted trade quality."""
        components = {
            "VWAP": 20 if market.vwap_distance_pct <= 0.25 and abs(market.vwap_slope) <= 0.03 else 8,
            "Opening Range": 15 if market.opening_range_pct <= 0.5 else 7,
            "VIX": 15 if market.india_vix <= self.settings.vix_threshold and abs(market.india_vix_change_pct) <= 3 else 5,
            "IV": 10 if market.iv_rank <= 65 else 4,
            "OI": 10 if 0.75 <= market.pcr <= 1.25 else 4,
            "PCR": 10 if 0.8 <= market.pcr <= 1.2 else 4,
            "News": 10 if not (market.rbi_policy or market.budget_day or market.major_global_event) else 0,
            "Time": 5 if market.timestamp.time() > time(9, 20) else 0,
            "Liquidity": 5 if not self._low_liquidity(market) else 0,
            "Premium Decay": 10 if market.premium_decay_started else 0,
        }
        score = min(100.0, float(sum(components.values())))
        if score >= 95:
            stars, label = "★★★★★", "Excellent"
        elif score >= 85:
            stars, label = "★★★★☆", "Good"
        elif score >= 75:
            stars, label = "★★★☆☆", "Average"
        else:
            stars, label = "☆☆☆☆☆", "NO TRADE"
        return TradeQuality(score, stars, label, components)

    def risk_plan(self, combined_premium: float, lot_size: int = 50, pop: float = 0.62) -> RiskPlan:
        """Build capital, stop, target, and risk/reward plan."""
        margin = self.settings.capital * 0.22
        max_risk = self.settings.capital * self.settings.risk_percent / 100
        target = combined_premium * self.settings.target_percent / 100 * lot_size
        expected_return = target / self.settings.capital * 100
        stop_levels = {f"{pct}%": round(combined_premium * (1 + pct / 100), 2) for pct in (30, 40, 50, 60)}
        risk_reward = round(target / max_risk, 2) if max_risk else 0.0
        return RiskPlan(self.settings.capital, margin, max_risk, combined_premium, round(target, 2), round(expected_return, 2), risk_reward, pop, stop_levels)

    def _low_liquidity(self, market: MarketSnapshot) -> bool:
        quotes = market.option_chain
        if not quotes:
            return True
        return any((q.ask - q.bid) / max(q.ltp, 1) > 0.03 or q.oi < 5000 or q.volume < 1000 for q in quotes)
