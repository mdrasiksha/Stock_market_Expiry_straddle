"""Broker abstraction ready for Zerodha, Dhan, Fyers, and Angel integrations."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class OrderRequest:
    """Normalized order request."""

    symbol: str
    side: str
    quantity: int
    order_type: str = "MARKET"
    price: float | None = None
    product: str = "MIS"


class Broker(ABC):
    """Broker interface for execution adapters."""

    @abstractmethod
    def place_order(self, order: OrderRequest) -> str: ...
    @abstractmethod
    def modify_order(self, order_id: str, **changes: Any) -> bool: ...
    @abstractmethod
    def cancel_order(self, order_id: str) -> bool: ...
    @abstractmethod
    def positions(self) -> list[dict[str, Any]]: ...
    @abstractmethod
    def orders(self) -> list[dict[str, Any]]: ...


@dataclass
class DummyBroker(Broker):
    """Paper-trading broker that records orders in memory."""

    _orders: list[dict[str, Any]] = field(default_factory=list)

    def place_order(self, order: OrderRequest) -> str:
        order_id = f"DUMMY-{uuid4().hex[:8]}"
        self._orders.append({"order_id": order_id, "status": "COMPLETE", "timestamp": datetime.now(), **order.__dict__})
        return order_id

    def modify_order(self, order_id: str, **changes: Any) -> bool:
        for order in self._orders:
            if order["order_id"] == order_id:
                order.update(changes)
                return True
        return False

    def cancel_order(self, order_id: str) -> bool:
        return self.modify_order(order_id, status="CANCELLED")

    def positions(self) -> list[dict[str, Any]]:
        return []

    def orders(self) -> list[dict[str, Any]]:
        return list(self._orders)
