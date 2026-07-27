"""Monitoring domain logic for short straddle positions."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from calculations import combined_premium, mtm, premium_decay, profit_percent, roi, sl_distance, stop_loss_premium, target_premium
from kite_api import ShortStraddle

TARGETS = (30, 50, 60, 70)
STOP_LOSSES = (10, 15, 20, 25)


@dataclass
class AlertState:
    """Tracks one-shot and dismissible alerts."""

    targets_triggered: set[int] = field(default_factory=set)
    stop_loss_triggered: bool = False
    alarm_dismissed: bool = False


@dataclass(frozen=True)
class MonitorSnapshot:
    """Current monitoring snapshot for UI rendering and journaling."""

    ce_price: float
    pe_price: float
    combined: float
    profit: float
    profit_pct: float
    decay_pct: float
    roi_pct: float
    target_rows: list[dict[str, object]]
    sl_rows: list[dict[str, object]]
    status: str
    reached_targets: list[int]
    stop_loss_hit: bool
    timestamp: datetime


class TradeMonitor:
    """Evaluates live option prices against profit targets and stop-loss levels."""

    def __init__(self, trade: ShortStraddle, margin: float | None = None) -> None:
        self.trade = trade
        self.margin = margin
        self.alert_state = AlertState()

    def snapshot(self, ce_price: float, pe_price: float) -> MonitorSnapshot:
        """Build a fresh monitoring snapshot from live CE and PE prices."""
        current = combined_premium(ce_price, pe_price)
        profit = mtm(self.trade.entry_premium, current, self.trade.quantity)
        profit_pct = profit_percent(self.trade.entry_premium, current)
        target_rows = []
        reached_targets = []
        for target in TARGETS:
            level = target_premium(self.trade.entry_premium, target)
            reached = current <= level
            if reached:
                reached_targets.append(target)
            target_rows.append({"Target": f"{target}%", "Target Premium": level, "Current Premium": current, "Status": "Reached" if reached else "Pending"})
        sl_rows = []
        stop_loss_hit = False
        for sl in STOP_LOSSES:
            level = stop_loss_premium(self.trade.entry_premium, sl)
            hit = current >= level
            stop_loss_hit = stop_loss_hit or hit
            sl_rows.append({"Stop Loss": f"{sl}%", "Current Level": level, "Distance Remaining": sl_distance(current, level), "Status": "Hit" if hit else "Safe"})
        status = "STOP LOSS" if stop_loss_hit else "BOOK PROFIT" if 70 in reached_targets else "HOLD"
        return MonitorSnapshot(
            ce_price=ce_price,
            pe_price=pe_price,
            combined=current,
            profit=profit,
            profit_pct=profit_pct,
            decay_pct=premium_decay(self.trade.entry_premium, current),
            roi_pct=roi(profit, self.margin),
            target_rows=target_rows,
            sl_rows=sl_rows,
            status=status,
            reached_targets=reached_targets,
            stop_loss_hit=stop_loss_hit,
            timestamp=datetime.now(),
        )

    def new_target_alerts(self, snapshot: MonitorSnapshot) -> list[int]:
        """Return newly reached targets and mark them triggered."""
        fresh = [target for target in snapshot.reached_targets if target not in self.alert_state.targets_triggered]
        self.alert_state.targets_triggered.update(fresh)
        return fresh

    def should_alarm(self, snapshot: MonitorSnapshot) -> bool:
        """Return True while stop loss is hit and alarm has not been dismissed."""
        if snapshot.stop_loss_hit:
            self.alert_state.stop_loss_triggered = True
        return snapshot.stop_loss_hit and not self.alert_state.alarm_dismissed
