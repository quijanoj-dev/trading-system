"""Abstract market data feed interfaces."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class OptionsFlow:
    ticker: str
    strike: float
    expiry: datetime
    option_type: str        # "call" or "put"
    size: int               # contracts
    premium: float          # total premium USD
    sentiment: str          # "bullish", "bearish", "neutral"
    is_sweep: bool
    timestamp: datetime
    exchange: str


@dataclass
class DarkPoolPrint:
    ticker: str
    price: float
    size: int               # shares
    notional: float         # USD value
    timestamp: datetime
    above_ask: bool         # True = buying, False = selling
    adv_pct: float          # % of average daily volume


@dataclass
class UnusualActivity:
    ticker: str
    activity_type: str      # "sweep", "block", "unusual_volume"
    description: str
    premium: Optional[float]
    timestamp: datetime
    confidence: float       # 0.0-1.0


class MarketDataFeed(ABC):
    """Abstract data feed. Implement for each data provider."""

    @abstractmethod
    def get_options_flow(self, ticker: str, limit: int = 50) -> List[OptionsFlow]:
        """Return recent options flow activity for ticker."""
        ...

    @abstractmethod
    def get_dark_pool_prints(self, ticker: str, limit: int = 20) -> List[DarkPoolPrint]:
        """Return recent dark pool prints for ticker."""
        ...

    @abstractmethod
    def get_unusual_activity(self, ticker: str, limit: int = 20) -> List[UnusualActivity]:
        """Return recent unusual activity alerts for ticker."""
        ...
