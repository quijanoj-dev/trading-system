"""Polymarket strategy base class and concrete implementations."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from execution.polymarket.connector import PolymarketMarket


@dataclass
class PolymarketSignal:
    market: PolymarketMarket
    direction: str          # "YES" or "NO"
    estimated_prob: float   # Claude / model estimate
    market_price: float     # current market price (same outcome)
    edge: float             # estimated_prob - market_price
    confidence: float       # 0.0-1.0
    rationale: str
    kelly_fraction: float   # raw Kelly (use fractional_kelly for sizing)

    def fractional_kelly(self, fraction: float = 0.25) -> float:
        return self.kelly_fraction * fraction


class PolymarketStrategy(ABC):
    """Base class for Polymarket trading strategies."""

    @abstractmethod
    def is_eligible(self, market: PolymarketMarket) -> bool:
        """Return True if this market is worth analyzing."""
        ...

    @abstractmethod
    def analyze(self, market: PolymarketMarket) -> Optional[PolymarketSignal]:
        """Return a signal if an edge exists, else None."""
        ...

    def size_position(self, signal: PolymarketSignal, account_value: float) -> float:
        """Size position using fractional Kelly, capped at 2% of account."""
        kelly = _kelly(signal.estimated_prob, signal.market_price)
        fractional = kelly * 0.25
        max_pct = 0.02
        return round(min(fractional, max_pct) * account_value, 2)


def _kelly(p: float, price: float) -> float:
    """Raw Kelly fraction.

    Args:
        p: Estimated true probability.
        price: Market implied probability (cost to buy).
    """
    if price <= 0 or price >= 1:
        return 0.0
    b = (1 - price) / price  # odds ratio
    q = 1 - p
    k = (p * b - q) / b
    return max(k, 0.0)


class ResolutionAmbiguityStrategy(PolymarketStrategy):
    """Target markets where resolution criteria are ambiguous.

    These markets are systematically mispriced because the crowd
    anchors to round numbers and ignores ambiguity risk.
    """

    MIN_VOLUME = 5_000      # USD minimum liquidity
    MIN_DAYS = 3
    MAX_DAYS = 60

    def is_eligible(self, market: PolymarketMarket) -> bool:
        from datetime import datetime, timezone
        try:
            end = datetime.fromisoformat(market.end_date.replace("Z", "+00:00"))
            days_left = (end - datetime.now(timezone.utc)).days
        except (ValueError, AttributeError):
            return False

        return (
            market.active
            and market.volume >= self.MIN_VOLUME
            and self.MIN_DAYS <= days_left <= self.MAX_DAYS
        )

    def analyze(self, market: PolymarketMarket) -> Optional[PolymarketSignal]:
        """Detect resolution ambiguity signals heuristically.

        Returns a NO signal when:
        - YES price > 0.85 (near-certainty) but question has vague criteria
        - Common ambiguity markers in question text
        """
        ambiguity_keywords = [
            "likely", "probably", "before or by", "at least",
            "significant", "substantially", "major", "notable",
        ]
        question_lower = market.question.lower()
        has_ambiguity = any(kw in question_lower for kw in ambiguity_keywords)

        # Near-certain YES with ambiguous criteria = SHORT YES (BUY NO)
        if has_ambiguity and market.yes_price > 0.85:
            estimated_no_prob = 0.20  # markets underestimate resolution risk
            edge = estimated_no_prob - market.no_price
            if edge < 0.05:
                return None

            kelly = _kelly(estimated_no_prob, market.no_price)
            return PolymarketSignal(
                market=market,
                direction="NO",
                estimated_prob=estimated_no_prob,
                market_price=market.no_price,
                edge=edge,
                confidence=0.5,
                rationale=f"Ambiguous resolution criteria + YES at {market.yes_price:.2f}",
                kelly_fraction=kelly,
            )
        return None


class LiquidityMispricingStrategy(PolymarketStrategy):
    """Target wide spreads on high-liquidity markets.

    When YES + NO prices don't sum to 1.0, there's a structural mispricing
    from automated market makers. Trade the cheaper side.
    """

    MIN_VOLUME = 50_000     # need real liquidity
    MAX_SPREAD_THRESHOLD = 0.05     # flag spreads > 5%

    def is_eligible(self, market: PolymarketMarket) -> bool:
        return market.active and market.volume >= self.MIN_VOLUME

    def analyze(self, market: PolymarketMarket) -> Optional[PolymarketSignal]:
        if market.spread < self.MAX_SPREAD_THRESHOLD:
            return None

        # Buy the cheaper outcome (spread arbitrage)
        if market.yes_price < market.no_price:
            direction = "YES"
            price = market.yes_price
            # If yes+no > 1, YES might be genuinely cheap
            estimated_prob = 1 - market.no_price
        else:
            direction = "NO"
            price = market.no_price
            estimated_prob = 1 - market.yes_price

        edge = estimated_prob - price
        if edge < 0.03:
            return None

        kelly = _kelly(estimated_prob, price)
        return PolymarketSignal(
            market=market,
            direction=direction,
            estimated_prob=estimated_prob,
            market_price=price,
            edge=edge,
            confidence=0.6,
            rationale=f"Spread={market.spread:.3f} on ${market.volume:,.0f} volume market",
            kelly_fraction=kelly,
        )
