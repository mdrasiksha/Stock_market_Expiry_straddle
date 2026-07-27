"""Zerodha Kite Connect integration layer."""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from kiteconnect import KiteConnect

from config import Settings, settings

logger = logging.getLogger(__name__)

SYMBOL_PATTERN = re.compile(r"^(?P<underlying>[A-Z]+)(?P<expiry>\d{2}[A-Z]{3}|\d{5})(?P<strike>\d+)(?P<option_type>CE|PE)$")


@dataclass(frozen=True)
class OptionLeg:
    """A single option leg detected from Zerodha positions."""

    trading_symbol: str
    exchange: str
    option_type: str
    strike: int
    expiry: str
    quantity: int
    average_price: float
    instrument_token: int | None = None


@dataclass(frozen=True)
class ShortStraddle:
    """Detected short straddle trade."""

    underlying: str
    expiry: str
    strike: int
    ce_leg: OptionLeg
    pe_leg: OptionLeg
    entry_time: datetime

    @property
    def quantity(self) -> int:
        """Return common absolute quantity for both short legs."""
        return min(abs(self.ce_leg.quantity), abs(self.pe_leg.quantity))

    @property
    def entry_premium(self) -> float:
        """Return combined entry premium."""
        return round(self.ce_leg.average_price + self.pe_leg.average_price, 2)


class KiteAPI:
    """High-level Kite Connect client with parsing and reconnect helpers."""

    def __init__(self, app_settings: Settings = settings) -> None:
        self.settings = app_settings
        self.kite = KiteConnect(api_key=app_settings.api_key) if app_settings.api_key else None
        if self.kite and app_settings.access_token:
            self.kite.set_access_token(app_settings.access_token)

    def login_url(self) -> str:
        """Return Kite login URL for manual token generation."""
        if not self.kite:
            return ""
        return self.kite.login_url()

    def is_logged_in(self) -> bool:
        """Return True if credentials are present and profile call succeeds."""
        if not self.kite or not self.settings.access_token:
            return False
        try:
            self.kite.profile()
            return True
        except Exception as exc:  # Kite exceptions vary by failure mode.
            logger.warning("Kite login check failed: %s", exc)
            return False

    def fetch_positions(self) -> list[dict[str, Any]]:
        """Fetch open net positions from Kite."""
        if not self.kite:
            return []
        try:
            positions = self.kite.positions().get("net", [])
            return [pos for pos in positions if pos.get("quantity", 0) != 0]
        except Exception as exc:
            logger.exception("Unable to fetch positions: %s", exc)
            return []

    def fetch_live_prices(self, symbols: list[str]) -> dict[str, float]:
        """Fetch last traded prices for exchange-qualified symbols."""
        if not self.kite or not symbols:
            return {}
        try:
            quote = self.kite.ltp(symbols)
            return {symbol: float(data["last_price"]) for symbol, data in quote.items()}
        except Exception as exc:
            logger.exception("Unable to fetch live prices: %s", exc)
            return {}

    def fetch_instrument_tokens(self, exchange: str = "NFO") -> dict[str, int]:
        """Fetch instrument token map for an exchange."""
        if not self.kite:
            return {}
        try:
            return {item["tradingsymbol"]: item["instrument_token"] for item in self.kite.instruments(exchange)}
        except Exception as exc:
            logger.exception("Unable to fetch instruments: %s", exc)
            return {}

    def detect_short_straddle(self, positions: list[dict[str, Any]] | None = None) -> ShortStraddle | None:
        """Detect the first matching short straddle from open short CE and PE positions."""
        positions = positions if positions is not None else self.fetch_positions()
        tokens = self.fetch_instrument_tokens()
        legs: dict[tuple[str, str, int], dict[str, OptionLeg]] = {}
        for pos in positions:
            qty = int(pos.get("quantity", 0))
            if qty >= 0:
                continue
            symbol = str(pos.get("tradingsymbol", ""))
            match = SYMBOL_PATTERN.match(symbol)
            if not match:
                continue
            key = (match.group("underlying"), match.group("expiry"), int(match.group("strike")))
            leg = OptionLeg(
                trading_symbol=symbol,
                exchange=str(pos.get("exchange", "NFO")),
                option_type=match.group("option_type"),
                strike=key[2],
                expiry=key[1],
                quantity=qty,
                average_price=float(pos.get("average_price", 0.0)),
                instrument_token=tokens.get(symbol),
            )
            legs.setdefault(key, {})[leg.option_type] = leg
        for (underlying, expiry, strike), pair in legs.items():
            if "CE" in pair and "PE" in pair:
                return ShortStraddle(underlying, expiry, strike, pair["CE"], pair["PE"], datetime.now())
        return None
