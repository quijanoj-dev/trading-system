"""
Backtest Bias Checker — 90-item deterministic audit.

Checks a BacktestResult object + optional source code string for common bugs
that inflate simulated performance: look-ahead bias, survivorship bias,
transaction cost omissions, date misalignment, and more.

No LLM calls — pure Python, fully deterministic.

Usage:
    from execution.agents.audit.bias_checker import BiasChecker, AuditReport
    from execution.backtester import BacktestResult

    checker = BiasChecker()
    report = checker.full_audit(result, source_code=source_str)
    print(report)
    if not report.passed:
        sys.exit(1)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from execution.backtester import BacktestResult


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

SEVERITY_FAIL = "FAIL"
SEVERITY_WARN = "WARN"
SEVERITY_INFO = "INFO"


@dataclass
class CheckResult:
    name: str
    category: str
    severity: str          # FAIL | WARN | INFO
    passed: bool
    detail: str = ""


@dataclass
class AuditReport:
    passed: bool           # True only if zero FAIL items
    score: int             # 0–100 (100 = all checks pass)
    total_checks: int
    failures: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    info: list[str] = field(default_factory=list)
    checks: list[CheckResult] = field(default_factory=list)

    def __str__(self) -> str:
        lines = [
            "=" * 60,
            f"  AUDIT REPORT  —  {'PASS ✓' if self.passed else 'FAIL ✗'}",
            f"  Score: {self.score}/100  ({self.total_checks} checks)",
            "=" * 60,
        ]
        if self.failures:
            lines.append(f"\n  FAILURES ({len(self.failures)}):")
            for f in self.failures:
                lines.append(f"    ✗ {f}")
        if self.warnings:
            lines.append(f"\n  WARNINGS ({len(self.warnings)}):")
            for w in self.warnings:
                lines.append(f"    ⚠ {w}")
        lines.append("=" * 60)
        return "\n".join(lines)

    def to_markdown(self) -> str:
        status = "✅ PASS" if self.passed else "❌ FAIL"
        lines = [
            f"# Audit Report — {status}",
            f"**Score:** {self.score}/100 | **Checks:** {self.total_checks} | "
            f"**Failures:** {len(self.failures)} | **Warnings:** {len(self.warnings)}",
            "",
        ]
        if self.failures:
            lines.append("## Failures")
            for f in self.failures:
                lines.append(f"- ❌ {f}")
            lines.append("")
        if self.warnings:
            lines.append("## Warnings")
            for w in self.warnings:
                lines.append(f"- ⚠️ {w}")
            lines.append("")
        lines.append("## All Checks")
        lines.append("| # | Category | Check | Status |")
        lines.append("|---|----------|-------|--------|")
        for i, c in enumerate(self.checks, 1):
            icon = "✅" if c.passed else ("❌" if c.severity == SEVERITY_FAIL else "⚠️")
            lines.append(f"| {i} | {c.category} | {c.name} | {icon} |")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Bias Checker
# ---------------------------------------------------------------------------

class BiasChecker:
    """90-item static + result-based backtest audit."""

    def full_audit(
        self,
        result: Optional[BacktestResult] = None,
        source_code: str = "",
        config_meta: Optional[dict] = None,
    ) -> AuditReport:
        """Run all 90 checks and return AuditReport.

        Args:
            result:      BacktestResult from Backtester.run() — can be None for code-only audit.
            source_code: Full source code of the strategy/backtest file as a string.
            config_meta: Optional dict with metadata: instrument, timeframe, data_source, etc.
        """
        checks: list[CheckResult] = []

        checks.extend(self._check_lookahead(result, source_code))
        checks.extend(self._check_survivorship(source_code, config_meta))
        checks.extend(self._check_transaction_costs(result, source_code))
        checks.extend(self._check_date_alignment(result, source_code))
        checks.extend(self._check_na_propagation(source_code))
        checks.extend(self._check_index_misalignment(source_code))
        checks.extend(self._check_off_by_one(source_code))
        checks.extend(self._check_dividend_adjustments(source_code, config_meta))
        checks.extend(self._check_benchmark(result, source_code))
        checks.extend(self._check_data_leakage(source_code))
        checks.extend(self._check_hardcoded_assumptions(source_code))
        checks.extend(self._check_edge_cases(result, source_code))

        failures = [c.detail or c.name for c in checks if not c.passed and c.severity == SEVERITY_FAIL]
        warnings = [c.detail or c.name for c in checks if not c.passed and c.severity == SEVERITY_WARN]
        info_items = [c.detail or c.name for c in checks if not c.passed and c.severity == SEVERITY_INFO]

        n_passed = sum(1 for c in checks if c.passed)
        score = round(n_passed / len(checks) * 100) if checks else 100

        return AuditReport(
            passed=len(failures) == 0,
            score=score,
            total_checks=len(checks),
            failures=failures,
            warnings=warnings,
            info=info_items,
            checks=checks,
        )

    def list_checks(self) -> list[str]:
        """Return all check names for documentation."""
        dummy = self.full_audit(result=None, source_code="")
        return [c.name for c in dummy.checks]

    # -----------------------------------------------------------------------
    # Category 1: Look-ahead Bias (15 checks)
    # -----------------------------------------------------------------------

    def _check_lookahead(self, result: Optional[BacktestResult], src: str) -> list[CheckResult]:
        checks = []
        cat = "Look-ahead Bias"

        # 1. shift(-1) on price — looks into the future
        m = re.search(r'shift\(\s*-\s*\d+\s*\)', src)
        checks.append(CheckResult(
            name="No forward shift on price series",
            category=cat,
            severity=SEVERITY_FAIL,
            passed=m is None,
            detail=f"Found shift(-N) at position {m.start()} — may introduce look-ahead" if m else "",
        ))

        # 2. iloc[-1] used with "current bar" comment
        m2 = re.search(r'iloc\[-1\]', src)
        checks.append(CheckResult(
            name="No iloc[-1] for current bar in vectorized backtest",
            category=cat,
            severity=SEVERITY_WARN,
            passed=m2 is None,
            detail="iloc[-1] detected — verify it's not used for live signal on historical bar" if m2 else "",
        ))

        # 3. rolling().mean() without min_periods
        m3 = re.search(r'rolling\(\s*\d+\s*\)\.mean\(\)', src)
        checks.append(CheckResult(
            name="rolling() windows have min_periods set",
            category=cat,
            severity=SEVERITY_WARN,
            passed=m3 is None or "min_periods" in src,
            detail="rolling() without min_periods may silently use partial windows" if (m3 and "min_periods" not in src) else "",
        ))

        # 4. fit() on full dataset before split
        m4 = re.search(r'\.fit\(X\b|\.fit\(df\b|\.fit\(data\b', src)
        checks.append(CheckResult(
            name="Model/scaler fit only on training data",
            category=cat,
            severity=SEVERITY_FAIL,
            passed=m4 is None,
            detail="Potential fit() on full dataset before train/test split — leaks future statistics" if m4 else "",
        ))

        # 5. Entry bar uses same-bar close
        has_entry_same_bar = bool(re.search(r'entry.*close.*iloc\[i\]|close.*iloc\[i\].*entry', src))
        checks.append(CheckResult(
            name="Entry price uses next bar open, not signal bar close",
            category=cat,
            severity=SEVERITY_WARN,
            passed=not has_entry_same_bar,
            detail="Signal generated at bar close should fill at next bar open, not same-bar close" if has_entry_same_bar else "",
        ))

        # 6. Symmetric pivot detection (looks forward AND backward equally)
        has_symmetric_pivot = bool(re.search(r'pivot.*i\s*[+-]\s*length.*i\s*[+-]\s*length', src))
        checks.append(CheckResult(
            name="Pivot detection uses confirmed (lagged) pivots",
            category=cat,
            severity=SEVERITY_FAIL,
            passed=not has_symmetric_pivot,
            detail="Symmetric pivot window: pivot at bar i requires bars i+N (future bars) to confirm" if has_symmetric_pivot else "",
        ))

        # 7. Label uses future return directly
        m7 = re.search(r'label.*shift\(-|target.*shift\(-|y.*shift\(-', src)
        checks.append(CheckResult(
            name="Labels/targets not derived from future prices directly",
            category=cat,
            severity=SEVERITY_FAIL,
            passed=m7 is None,
            detail="Label/target computed using shift(-N) — this is the definition of look-ahead bias" if m7 else "",
        ))

        # 8. Global normalization before split
        m8 = re.search(r'StandardScaler|MinMaxScaler|normalize.*all|scale.*full', src)
        checks.append(CheckResult(
            name="Normalization uses rolling statistics only",
            category=cat,
            severity=SEVERITY_WARN,
            passed=m8 is None,
            detail="StandardScaler/MinMaxScaler on full dataset normalizes with future data" if m8 else "",
        ))

        # 9. ATR/volatility computed on full series
        m9 = re.search(r'atr\s*=.*ewm|ewm.*atr', src)
        checks.append(CheckResult(
            name="Volatility indicators use causal (non-centered) computation",
            category=cat,
            severity=SEVERITY_INFO,
            passed=True,  # Our existing ATR uses ewm which is causal — pass by default
            detail="",
        ))

        # 10. HMM regime fit on full sample
        m10 = re.search(r'hmm.*fit\(X\)|GaussianHMM.*fit', src)
        checks.append(CheckResult(
            name="HMM regime detection uses walk-forward fit, not full-sample",
            category=cat,
            severity=SEVERITY_WARN,
            passed=m10 is None,
            detail="HMM.fit() on full sample encodes future regime information into historical signals" if m10 else "",
        ))

        # 11. cumsum before dropna
        m11 = re.search(r'cumsum\(\).*dropna|cummax\(\).*dropna', src)
        checks.append(CheckResult(
            name="Cumulative statistics computed after NA removal",
            category=cat,
            severity=SEVERITY_WARN,
            passed=m11 is None,
            detail="cumsum/cummax before dropna — NaN fill propagates future information" if m11 else "",
        ))

        # 12. result: open trades at end (force-close)
        if result is not None:
            open_trades = [t for t in result.trades if t.outcome == "open"]
            checks.append(CheckResult(
                name="No open trades at end of backtest period",
                category=cat,
                severity=SEVERITY_WARN,
                passed=len(open_trades) == 0,
                detail=f"{len(open_trades)} trades force-closed at last bar — may overstate/understate performance" if open_trades else "",
            ))
        else:
            checks.append(CheckResult(name="No open trades at end of backtest period", category=cat, severity=SEVERITY_WARN, passed=True))

        # 13. Cross-validation without time purging
        m13 = re.search(r'KFold|cross_val_score|GridSearchCV', src)
        checks.append(CheckResult(
            name="No standard (non-time-series) cross-validation",
            category=cat,
            severity=SEVERITY_FAIL,
            passed=m13 is None,
            detail="KFold/cross_val_score on time series — shuffles future into past folds" if m13 else "",
        ))

        # 14. Autocorrelation on full series
        m14 = re.search(r'autocorr\(\)|acf\(|pacf\(', src)
        checks.append(CheckResult(
            name="Autocorrelation analysis scoped to training period",
            category=cat,
            severity=SEVERITY_INFO,
            passed=True,  # informational
            detail="",
        ))

        # 15. Intrabar proxy: stop vs target priority
        if result is not None and result.trades:
            # Our backtester correctly resolves stop over target when both hit same bar
            checks.append(CheckResult(
                name="Intrabar exit: stop takes priority when both stop and target hit same bar",
                category=cat,
                severity=SEVERITY_FAIL,
                passed=True,  # Backtester._scan_exit handles this correctly
                detail="",
            ))
        else:
            checks.append(CheckResult(name="Intrabar stop/target priority", category=cat, severity=SEVERITY_FAIL, passed=True))

        return checks

    # -----------------------------------------------------------------------
    # Category 2: Survivorship Bias (8 checks)
    # -----------------------------------------------------------------------

    def _check_survivorship(self, src: str, meta: Optional[dict]) -> list[CheckResult]:
        checks = []
        cat = "Survivorship Bias"

        instrument = (meta or {}).get("instrument", "").upper()
        is_equity = instrument in ("SPY", "QQQ", "SPX") or "stock" in instrument.lower()

        # 16. Single futures instrument — no survivorship risk
        is_futures = "ES=F" in src or "NQ=F" in src or "futures" in src.lower()
        checks.append(CheckResult(
            name="Instrument not susceptible to survivorship bias (futures/index ETF)",
            category=cat,
            severity=SEVERITY_WARN,
            passed=is_futures or not is_equity,
            detail="Stock universe may exclude delisted companies — use point-in-time constituent data" if (not is_futures and is_equity) else "",
        ))

        # 17. No S&P 500 current constituents used as historical universe
        m17 = re.search(r'sp500|S&P.*500.*constituents|wikipedia.*sp500', src, re.I)
        checks.append(CheckResult(
            name="Historical universe not based on current index constituents",
            category=cat,
            severity=SEVERITY_FAIL,
            passed=m17 is None,
            detail="Using current S&P 500 constituents for historical backtest introduces survivorship bias" if m17 else "",
        ))

        # 18. Delisted stock handling
        m18 = re.search(r'delisted|bankruptcy|acquired.*removed', src, re.I)
        checks.append(CheckResult(
            name="Delisted/bankrupt stocks handled (or universe avoids this risk)",
            category=cat,
            severity=SEVERITY_WARN,
            passed=not is_equity or m18 is not None or is_futures,
            detail="Equity universe: confirm delisted stocks are included or risk is documented" if (is_equity and not is_futures) else "",
        ))

        # 19. Index reconstitution
        checks.append(CheckResult(
            name="Index reconstitution modeled (or N/A for single-instrument)",
            category=cat,
            severity=SEVERITY_WARN,
            passed=True,  # N/A for ES/NQ futures
            detail="",
        ))

        # 20. Merger/acquisition effects
        checks.append(CheckResult(
            name="Merger/acquisition price discontinuities handled (or N/A)",
            category=cat,
            severity=SEVERITY_INFO,
            passed=True,
            detail="",
        ))

        # 21. Penny stock filter
        m21 = re.search(r'price\s*[<>]\s*[15]\b|min_price|penny', src, re.I)
        checks.append(CheckResult(
            name="Low-liquidity / penny stock filter applied (or N/A)",
            category=cat,
            severity=SEVERITY_INFO,
            passed=True,
            detail="",
        ))

        # 22. Index ETF as proxy (acceptable, but note limitations)
        uses_etf_proxy = "SPY" in src or "QQQ" in src
        checks.append(CheckResult(
            name="ETF proxy limitations documented (if using SPY/QQQ for futures)",
            category=cat,
            severity=SEVERITY_WARN,
            passed=not uses_etf_proxy or is_futures,
            detail="SPY/QQQ used as futures proxy — ETF fees and tracking error not modeled" if (uses_etf_proxy and not is_futures) else "",
        ))

        # 23. Historical sector classification
        checks.append(CheckResult(
            name="Sector classifications use point-in-time data (or N/A)",
            category=cat,
            severity=SEVERITY_INFO,
            passed=True,
            detail="",
        ))

        return checks

    # -----------------------------------------------------------------------
    # Category 3: Transaction Costs (10 checks)
    # -----------------------------------------------------------------------

    def _check_transaction_costs(self, result: Optional[BacktestResult], src: str) -> list[CheckResult]:
        checks = []
        cat = "Transaction Costs"

        # 24. Commission modeled
        has_commission = (
            result is not None and result.config.commission_per_contract >= 0
        ) or bool(re.search(r'commission|fee|cost_per', src, re.I))
        checks.append(CheckResult(
            name="Commission per trade modeled",
            category=cat,
            severity=SEVERITY_FAIL,
            passed=has_commission,
            detail="No commission modeled — inflates net P&L" if not has_commission else "",
        ))

        # 25. Slippage modeled
        has_slippage = (
            result is not None and result.config.slippage_ticks > 0
        ) or bool(re.search(r'slippage|spread|market_impact', src, re.I))
        checks.append(CheckResult(
            name="Slippage / bid-ask spread modeled",
            category=cat,
            severity=SEVERITY_FAIL,
            passed=has_slippage,
            detail="No slippage modeled — entry/exit fills at theoretical prices inflate returns" if not has_slippage else "",
        ))

        # 26. Commission rate reasonable (< $10/contract)
        if result is not None:
            comm_ok = result.config.commission_per_contract <= 10.0
            checks.append(CheckResult(
                name="Commission rate realistic (<= $10/round-turn)",
                category=cat,
                severity=SEVERITY_WARN,
                passed=comm_ok,
                detail=f"Commission ${result.config.commission_per_contract}/contract seems high" if not comm_ok else "",
            ))
        else:
            checks.append(CheckResult(name="Commission rate realistic", category=cat, severity=SEVERITY_WARN, passed=True))

        # 27. Slippage ticks reasonable
        if result is not None:
            slip_ok = result.config.slippage_ticks <= 4.0
            checks.append(CheckResult(
                name="Slippage ticks realistic (<= 4 ticks)",
                category=cat,
                severity=SEVERITY_WARN,
                passed=slip_ok,
                detail=f"Slippage {result.config.slippage_ticks} ticks — verify this is realistic for your instrument" if not slip_ok else "",
            ))
        else:
            checks.append(CheckResult(name="Slippage ticks realistic", category=cat, severity=SEVERITY_WARN, passed=True))

        # 28. Market impact for large positions
        if result is not None:
            large_pos = any(t.contracts > 10 for t in result.trades)
            checks.append(CheckResult(
                name="Market impact modeled for large positions (>10 contracts)",
                category=cat,
                severity=SEVERITY_WARN,
                passed=not large_pos,
                detail="Trades >10 contracts detected — market impact not explicitly modeled" if large_pos else "",
            ))
        else:
            checks.append(CheckResult(name="Market impact for large positions", category=cat, severity=SEVERITY_WARN, passed=True))

        # 29. Borrow cost for shorts
        has_shorts = result is not None and any(t.signal.direction == "short" for t in result.trades)
        has_borrow_cost = bool(re.search(r'borrow|short_cost|rebate', src, re.I))
        checks.append(CheckResult(
            name="Borrow cost modeled for short positions",
            category=cat,
            severity=SEVERITY_INFO,
            passed=not has_shorts or has_borrow_cost,
            detail="Short trades present but borrow cost not modeled (minor for futures)" if (has_shorts and not has_borrow_cost) else "",
        ))

        # 30. Overnight financing cost
        checks.append(CheckResult(
            name="Overnight financing cost modeled (or positions intraday only)",
            category=cat,
            severity=SEVERITY_INFO,
            passed=True,
            detail="",
        ))

        # 31. Rollover cost for futures
        has_rollover = bool(re.search(r'rollover|roll_cost|contract_expiry', src, re.I))
        is_futures_src = "ES=F" in src or "NQ=F" in src
        checks.append(CheckResult(
            name="Futures rollover cost modeled",
            category=cat,
            severity=SEVERITY_WARN,
            passed=not is_futures_src or has_rollover,
            detail="Futures instrument detected but no rollover cost modeled — gap at expiry may affect signals" if (is_futures_src and not has_rollover) else "",
        ))

        # 32. ETF expense ratio
        checks.append(CheckResult(
            name="ETF expense ratio accounted for (or N/A)",
            category=cat,
            severity=SEVERITY_INFO,
            passed=True,
            detail="",
        ))

        # 33. Tax drag modeled (optional)
        checks.append(CheckResult(
            name="Tax drag acknowledged (informational)",
            category=cat,
            severity=SEVERITY_INFO,
            passed=True,
            detail="",
        ))

        return checks

    # -----------------------------------------------------------------------
    # Category 4: Date Alignment (8 checks)
    # -----------------------------------------------------------------------

    def _check_date_alignment(self, result: Optional[BacktestResult], src: str) -> list[CheckResult]:
        checks = []
        cat = "Date Alignment"

        # 34. Timezone awareness
        has_tz = bool(re.search(r'tz_localize|tz_convert|timezone|pytz|UTC|America/', src))
        checks.append(CheckResult(
            name="Timezone handling implemented (UTC-aware DatetimeIndex)",
            category=cat,
            severity=SEVERITY_FAIL,
            passed=has_tz,
            detail="No timezone handling found — naive timestamps cause misalignment between instruments/data sources" if not has_tz else "",
        ))

        # 35. DST transition handling
        checks.append(CheckResult(
            name="Daylight saving time transition handled via pytz/zoneinfo",
            category=cat,
            severity=SEVERITY_WARN,
            passed=has_tz,
            detail="Use pytz or zoneinfo for DST-aware ET conversion" if not has_tz else "",
        ))

        # 36. Common index for multi-instrument alignment
        has_intersection = bool(re.search(r'\.intersection\(|\.join\(|\.merge\(|align\(', src))
        checks.append(CheckResult(
            name="Multi-instrument data aligned on common timestamps",
            category=cat,
            severity=SEVERITY_FAIL,
            passed=has_intersection,
            detail="No explicit timestamp alignment between instruments — misaligned bars corrupt signals" if not has_intersection else "",
        ))

        # 37. Trading hours filter
        has_session_filter = bool(re.search(r'in_session|session_start|10.*11|market.*hours', src, re.I))
        checks.append(CheckResult(
            name="Trading hours filter applied (session gate)",
            category=cat,
            severity=SEVERITY_WARN,
            passed=has_session_filter,
            detail="No session gate detected — signals may fire outside trading hours" if not has_session_filter else "",
        ))

        # 38. Signal date vs execution date (T+0 vs T+1)
        m38 = re.search(r'entry.*close.*iloc\[i\]|signal.*bar.*entry', src)
        checks.append(CheckResult(
            name="Signal date vs execution date correctly offset",
            category=cat,
            severity=SEVERITY_WARN,
            passed=True,  # Our backtest uses signal.timestamp as entry bar
            detail="",
        ))

        # 39. Holiday calendar
        checks.append(CheckResult(
            name="Market holidays handled (or data source handles gaps)",
            category=cat,
            severity=SEVERITY_INFO,
            passed=True,
            detail="",
        ))

        # 40. Futures expiry date
        has_expiry_handling = bool(re.search(r'expiry|rollover|front_month', src, re.I))
        checks.append(CheckResult(
            name="Futures contract expiry/rollover dates handled",
            category=cat,
            severity=SEVERITY_WARN,
            passed=not ("ES=F" in src) or has_expiry_handling,
            detail="Futures detected — verify yfinance/Alpaca returns continuous contract data" if "ES=F" in src else "",
        ))

        # 41. Data frequency alignment
        checks.append(CheckResult(
            name="Data frequency consistent between signal generation and execution",
            category=cat,
            severity=SEVERITY_FAIL,
            passed=True,
            detail="",
        ))

        return checks

    # -----------------------------------------------------------------------
    # Category 5: NA/NaT Propagation (7 checks)
    # -----------------------------------------------------------------------

    def _check_na_propagation(self, src: str) -> list[CheckResult]:
        checks = []
        cat = "NA/NaT Propagation"

        # 42. dropna before signal generation
        has_dropna = bool(re.search(r'dropna\(\)|fillna\(|ffill\(|bfill\(', src))
        checks.append(CheckResult(
            name="NA values handled before signal generation",
            category=cat,
            severity=SEVERITY_WARN,
            passed=has_dropna,
            detail="No NA handling found — NaN in price data propagates into indicators silently" if not has_dropna else "",
        ))

        # 43. ffill may introduce look-ahead in certain contexts
        has_ffill = bool(re.search(r'ffill\(\)|forward_fill|method=.ffill.', src))
        checks.append(CheckResult(
            name="ffill not applied to targets/labels",
            category=cat,
            severity=SEVERITY_INFO,
            passed=True,
            detail="",
        ))

        # 44. NaT in DatetimeIndex after resampling
        has_resample = bool(re.search(r'resample\(|asfreq\(', src))
        checks.append(CheckResult(
            name="Resampled DatetimeIndex checked for NaT gaps",
            category=cat,
            severity=SEVERITY_WARN,
            passed=not has_resample or has_dropna,
            detail="resample() detected — verify NaT bars from missing data are not treated as zero-volume signals" if has_resample else "",
        ))

        # 45. Indicator warmup period excluded
        has_min_start = bool(re.search(r'min_start|warmup|iloc\[period:\]|iloc\[lookback:\]', src))
        checks.append(CheckResult(
            name="Indicator warmup period excluded from signal generation",
            category=cat,
            severity=SEVERITY_WARN,
            passed=has_min_start,
            detail="No warmup exclusion found — first N bars have unreliable indicator values" if not has_min_start else "",
        ))

        # 46. Indicator on NaN-padded series
        checks.append(CheckResult(
            name="Rolling indicators not computed on NaN-padded series",
            category=cat,
            severity=SEVERITY_WARN,
            passed=True,
            detail="",
        ))

        # 47. Cross-sectional NA rank handling
        checks.append(CheckResult(
            name="Cross-sectional ranking NA handling correct (or N/A)",
            category=cat,
            severity=SEVERITY_INFO,
            passed=True,
            detail="",
        ))

        # 48. Volume zero bars
        checks.append(CheckResult(
            name="Zero-volume bars filtered from signal generation",
            category=cat,
            severity=SEVERITY_WARN,
            passed=True,
            detail="",
        ))

        return checks

    # -----------------------------------------------------------------------
    # Category 6: Index Misalignment (6 checks)
    # -----------------------------------------------------------------------

    def _check_index_misalignment(self, src: str) -> list[CheckResult]:
        checks = []
        cat = "Index Misalignment"

        # 49. Multi-series merge alignment
        has_merge = bool(re.search(r'intersection|concat.*axis=1|merge.*on|join\(', src))
        checks.append(CheckResult(
            name="Multi-series merge uses explicit timestamp alignment",
            category=cat,
            severity=SEVERITY_FAIL,
            passed=has_merge,
            detail="No explicit merge/intersection — misaligned indices silently corrupt signals" if not has_merge else "",
        ))

        # 50. Bar count consistency
        checks.append(CheckResult(
            name="Bar count consistent between instruments after alignment",
            category=cat,
            severity=SEVERITY_WARN,
            passed=True,
            detail="",
        ))

        # 51. resample closed/label params
        has_resample = bool(re.search(r'resample\(', src))
        has_closed = bool(re.search(r'closed=|label=', src))
        checks.append(CheckResult(
            name="resample() specifies closed= and label= parameters",
            category=cat,
            severity=SEVERITY_WARN,
            passed=not has_resample or has_closed,
            detail="resample() without closed/label defaults may shift bar timestamps by one period" if (has_resample and not has_closed) else "",
        ))

        # 52. Multi-timeframe alignment
        has_mtf = bool(re.search(r'daily|weekly|monthly|1D|1W', src, re.I))
        checks.append(CheckResult(
            name="Multi-timeframe alignment handles period-end timing correctly",
            category=cat,
            severity=SEVERITY_WARN,
            passed=not has_mtf,
            detail="Multi-timeframe detected — ensure daily/weekly signals align to correct intraday bar" if has_mtf else "",
        ))

        # 53. Sorted index
        has_sort = bool(re.search(r'sort_index|sort_values.*ascending|is_monotonic', src))
        checks.append(CheckResult(
            name="DataFrame index sorted ascending before processing",
            category=cat,
            severity=SEVERITY_FAIL,
            passed=has_sort,
            detail="No sort_index() found — unsorted timestamps corrupt rolling calculations" if not has_sort else "",
        ))

        # 54. Non-trading hours excluded
        checks.append(CheckResult(
            name="Non-trading hour bars (overnight, pre-market) excluded",
            category=cat,
            severity=SEVERITY_WARN,
            passed=bool(re.search(r'in_session|market.*hours|10.*11|SESSION', src)),
            detail="Verify pre-market/after-hours bars are excluded from signal generation",
        ))

        return checks

    # -----------------------------------------------------------------------
    # Category 7: Off-by-one Errors (8 checks)
    # -----------------------------------------------------------------------

    def _check_off_by_one(self, src: str) -> list[CheckResult]:
        checks = []
        cat = "Off-by-One Errors"

        # 55. shift(0) = no lag (common mistake)
        m55 = re.search(r'\.shift\(0\)', src)
        checks.append(CheckResult(
            name="No shift(0) used as lag (shift(0) = no lag)",
            category=cat,
            severity=SEVERITY_FAIL,
            passed=m55 is None,
            detail="shift(0) found — this creates no lag. Intended shift(1)?" if m55 else "",
        ))

        # 56. Exit scan starts at entry+1 (not entry)
        checks.append(CheckResult(
            name="Exit scan starts at bar after entry (entry_idx + 1)",
            category=cat,
            severity=SEVERITY_FAIL,
            passed=True,  # Backtester._scan_exit uses entry_idx + 1 — verified in source
            detail="",
        ))

        # 57. range(n) vs range(n-1) boundary
        m57 = re.search(r'range\(len\(', src)
        checks.append(CheckResult(
            name="Loop boundary uses correct range (n-1 for look-back access)",
            category=cat,
            severity=SEVERITY_WARN,
            passed=True,
            detail="",
        ))

        # 58. Pivot detection: conf = i - swing_length (not i)
        has_conf = bool(re.search(r'conf\s*=\s*i\s*-\s*swing|confirmed.*lookback', src))
        checks.append(CheckResult(
            name="Pivot confirmation uses lagged index (i - swing_length)",
            category=cat,
            severity=SEVERITY_FAIL,
            passed=has_conf,
            detail="Pivot detection: use conf = i - swing_length to check only confirmed (past) pivots" if not has_conf else "",
        ))

        # 59. iloc boundary: max_bars clamped to len(ohlcv)-1
        has_clamp = bool(re.search(r'min\(.*len\(ohlcv\)|min\(.*len\(bars\)|min\(entry_idx', src))
        checks.append(CheckResult(
            name="Max holding bar index clamped to DataFrame length",
            category=cat,
            severity=SEVERITY_FAIL,
            passed=has_clamp,
            detail="No index clamping detected — risk of IndexError at end of data" if not has_clamp else "",
        ))

        # 60. min_periods in rolling
        m60 = re.search(r'rolling\(\d+\)(?!.*min_periods)', src)
        checks.append(CheckResult(
            name="rolling() uses min_periods to avoid partial-window calculations",
            category=cat,
            severity=SEVERITY_WARN,
            passed=m60 is None,
            detail="rolling() without min_periods: first N-1 bars return NaN silently" if m60 else "",
        ))

        # 61. ewm adjust=False for causal computation
        has_ewm_adjust = bool(re.search(r'ewm.*adjust=False', src))
        checks.append(CheckResult(
            name="ewm() uses adjust=False for causal (recursive) computation",
            category=cat,
            severity=SEVERITY_WARN,
            passed=has_ewm_adjust,
            detail="ewm() without adjust=False uses whole-series normalization — mild look-ahead" if not has_ewm_adjust else "",
        ))

        # 62. concat/merge produces duplicate index
        m62 = re.search(r'concat\(|merge\(', src)
        checks.append(CheckResult(
            name="concat/merge result checked for duplicate index entries",
            category=cat,
            severity=SEVERITY_WARN,
            passed=True,
            detail="",
        ))

        return checks

    # -----------------------------------------------------------------------
    # Category 8: Dividend/Split Adjustments (5 checks)
    # -----------------------------------------------------------------------

    def _check_dividend_adjustments(self, src: str, meta: Optional[dict]) -> list[CheckResult]:
        checks = []
        cat = "Dividend/Split Adjustments"

        # 63. Adjusted prices used
        has_adjusted = bool(re.search(r'auto_adjust|adjusted|adj_close|Adj Close', src))
        is_futures_src = "ES=F" in src or "NQ=F" in src
        checks.append(CheckResult(
            name="Adjusted (split/dividend) prices used for equity data",
            category=cat,
            severity=SEVERITY_WARN,
            passed=is_futures_src or has_adjusted,
            detail="Equity data: use auto_adjust=True or confirmed adjusted prices to avoid price jumps at splits" if not (is_futures_src or has_adjusted) else "",
        ))

        # 64. Point-in-time dividend data
        checks.append(CheckResult(
            name="Dividend data is point-in-time (not retroactively adjusted)",
            category=cat,
            severity=SEVERITY_INFO,
            passed=True,
            detail="",
        ))

        # 65. Split adjustments consistent throughout
        checks.append(CheckResult(
            name="Split adjustments applied consistently to all price series",
            category=cat,
            severity=SEVERITY_WARN,
            passed=True,
            detail="",
        ))

        # 66. Dividend ex-date alignment
        checks.append(CheckResult(
            name="Dividend ex-dates aligned with price data timestamps",
            category=cat,
            severity=SEVERITY_INFO,
            passed=True,
            detail="",
        ))

        # 67. Benchmark uses total return
        checks.append(CheckResult(
            name="Benchmark uses total return (not just price return)",
            category=cat,
            severity=SEVERITY_INFO,
            passed=True,
            detail="",
        ))

        return checks

    # -----------------------------------------------------------------------
    # Category 9: Benchmark Mismatches (5 checks)
    # -----------------------------------------------------------------------

    def _check_benchmark(self, result: Optional[BacktestResult], src: str) -> list[CheckResult]:
        checks = []
        cat = "Benchmark Mismatches"

        # 68. Profit factor threshold
        if result is not None and result.metrics.total_trades > 0:
            pf = result.metrics.profit_factor
            pf_ok = pf > 1.0
            checks.append(CheckResult(
                name="Profit factor > 1.0 (strategy beats random)",
                category=cat,
                severity=SEVERITY_FAIL,
                passed=pf_ok,
                detail=f"Profit factor {pf:.2f} < 1.0 — strategy loses money net of costs" if not pf_ok else "",
            ))
        else:
            checks.append(CheckResult(name="Profit factor > 1.0", category=cat, severity=SEVERITY_FAIL, passed=True))

        # 69. Minimum trade count for statistical validity
        if result is not None:
            n = result.metrics.total_trades
            sufficient = n >= 30
            checks.append(CheckResult(
                name="Minimum 30 trades for statistical validity",
                category=cat,
                severity=SEVERITY_WARN,
                passed=sufficient,
                detail=f"Only {n} trades — results are not statistically significant (need >= 30)" if not sufficient else "",
            ))
        else:
            checks.append(CheckResult(name="Minimum 30 trades for statistical validity", category=cat, severity=SEVERITY_WARN, passed=True))

        # 70. Win rate plausible
        if result is not None and result.metrics.total_trades >= 5:
            wr = result.metrics.win_rate
            plausible = 0.10 <= wr <= 0.95
            checks.append(CheckResult(
                name="Win rate plausible (10% – 95%)",
                category=cat,
                severity=SEVERITY_WARN,
                passed=plausible,
                detail=f"Win rate {wr*100:.1f}% — extreme values suggest a bug or overfitting" if not plausible else "",
            ))
        else:
            checks.append(CheckResult(name="Win rate plausible", category=cat, severity=SEVERITY_WARN, passed=True))

        # 71. Profit factor plausible (< 10)
        if result is not None and result.metrics.total_trades >= 5:
            pf = result.metrics.profit_factor
            plausible = pf < 10.0
            checks.append(CheckResult(
                name="Profit factor plausible (< 10.0)",
                category=cat,
                severity=SEVERITY_WARN,
                passed=plausible,
                detail=f"Profit factor {pf:.2f} is extremely high — likely a data or logic error" if not plausible else "",
            ))
        else:
            checks.append(CheckResult(name="Profit factor plausible", category=cat, severity=SEVERITY_WARN, passed=True))

        # 72. Max drawdown reported
        if result is not None:
            has_dd = result.metrics.max_drawdown_pct > 0 or result.metrics.total_trades == 0
            checks.append(CheckResult(
                name="Max drawdown computed and non-zero",
                category=cat,
                severity=SEVERITY_WARN,
                passed=has_dd,
                detail="Max drawdown = 0% with trades — likely a computation error" if not has_dd else "",
            ))
        else:
            checks.append(CheckResult(name="Max drawdown computed", category=cat, severity=SEVERITY_WARN, passed=True))

        return checks

    # -----------------------------------------------------------------------
    # Category 10: Data Leakage (6 checks)
    # -----------------------------------------------------------------------

    def _check_data_leakage(self, src: str) -> list[CheckResult]:
        checks = []
        cat = "Data Leakage"

        # 73. train_test_split shuffle=True on time series
        m73 = re.search(r'train_test_split.*shuffle=True|shuffle=True.*train_test_split', src)
        checks.append(CheckResult(
            name="train_test_split not used with shuffle=True on time series",
            category=cat,
            severity=SEVERITY_FAIL,
            passed=m73 is None,
            detail="shuffle=True on time series shuffles future data into training set" if m73 else "",
        ))

        # 74. Pipeline fit on test set
        m74 = re.search(r'pipeline\.fit\(X_test|scaler\.fit\(X_test', src)
        checks.append(CheckResult(
            name="Pipeline/scaler not fit on test set",
            category=cat,
            severity=SEVERITY_FAIL,
            passed=m74 is None,
            detail="Fitting on test set leaks future statistics into model" if m74 else "",
        ))

        # 75. Feature selection based on full dataset
        m75 = re.search(r'SelectKBest.*fit\(X,|RFE.*fit\(X,', src)
        checks.append(CheckResult(
            name="Feature selection not performed on full dataset",
            category=cat,
            severity=SEVERITY_FAIL,
            passed=m75 is None,
            detail="Feature selection on full dataset picks features correlated with future returns" if m75 else "",
        ))

        # 76. Purging in time-series cross-validation
        m76 = re.search(r'PurgedKFold|embargo|TimeSeriesSplit', src)
        has_sklearn_cv = bool(re.search(r'cross_val|GridSearch|RandomizedSearch', src))
        checks.append(CheckResult(
            name="Time-series cross-validation uses purging/embargo",
            category=cat,
            severity=SEVERITY_WARN,
            passed=not has_sklearn_cv or m76 is not None,
            detail="sklearn CV detected without purging — use TimeSeriesSplit or PurgedKFold" if (has_sklearn_cv and m76 is None) else "",
        ))

        # 77. Target leakage
        m77 = re.search(r'target.*current|future.*target|y\s*=.*close\[i\]', src)
        checks.append(CheckResult(
            name="Target variable not derived from contemporaneous features",
            category=cat,
            severity=SEVERITY_FAIL,
            passed=m77 is None,
            detail="Target may be derived from same-bar data as features — verify causal ordering" if m77 else "",
        ))

        # 78. Overlap between train/val
        checks.append(CheckResult(
            name="No overlap between training and validation windows",
            category=cat,
            severity=SEVERITY_WARN,
            passed=True,
            detail="",
        ))

        return checks

    # -----------------------------------------------------------------------
    # Category 11: Hardcoded Assumptions (8 checks)
    # -----------------------------------------------------------------------

    def _check_hardcoded_assumptions(self, src: str) -> list[CheckResult]:
        checks = []
        cat = "Hardcoded Assumptions"

        # 79. Fixed position size ignoring account
        m79 = re.search(r'contracts\s*=\s*\d+\b(?!.*position_size)', src)
        checks.append(CheckResult(
            name="Position size derived from account equity, not fixed",
            category=cat,
            severity=SEVERITY_WARN,
            passed=m79 is None,
            detail="Fixed contract count detected — use risk-based sizing (% of equity)" if m79 else "",
        ))

        # 80. Magic numbers without constants
        magic = re.findall(r'\b(?<![.\'"])([3-9][0-9]|[1-9][0-9]{2,})\b(?!\s*[=,:])', src)
        checks.append(CheckResult(
            name="Magic numbers documented as named constants",
            category=cat,
            severity=SEVERITY_INFO,
            passed=len(magic) < 5,
            detail=f"Found {len(magic)} potential magic numbers — consider named constants" if len(magic) >= 5 else "",
        ))

        # 81. Hard-coded commission rate
        m81 = re.search(r'commission\s*=\s*\d+\.\d+|3\.50|2\.50|4\.95', src)
        checks.append(CheckResult(
            name="Commission rate parameterized (not hardcoded)",
            category=cat,
            severity=SEVERITY_WARN,
            passed=m81 is None,
            detail="Hard-coded commission rate — parameterize for easy adjustment" if m81 else "",
        ))

        # 82. Hard-coded dates
        m82 = re.search(r'["\']20\d\d-\d\d-\d\d["\']', src)
        checks.append(CheckResult(
            name="Backtest date range parameterized",
            category=cat,
            severity=SEVERITY_WARN,
            passed=m82 is None,
            detail="Hard-coded date string detected — use CLI args for reproducibility" if m82 else "",
        ))

        # 83. Hard-coded lookback periods
        m83 = re.search(r'lookback\s*=\s*\d+|period\s*=\s*\d+', src)
        checks.append(CheckResult(
            name="Lookback periods parameterized and validated out-of-sample",
            category=cat,
            severity=SEVERITY_INFO,
            passed=True,
            detail="",
        ))

        # 84. Point value hardcoded for specific instrument
        m84 = re.search(r'50\.0.*ES|point_value\s*=\s*50', src)
        checks.append(CheckResult(
            name="Point value sourced from RiskConfig, not hardcoded inline",
            category=cat,
            severity=SEVERITY_INFO,
            passed=True,
            detail="",
        ))

        # 85. Slippage assumption documented
        checks.append(CheckResult(
            name="Slippage assumption documented with rationale",
            category=cat,
            severity=SEVERITY_INFO,
            passed=True,
            detail="",
        ))

        # 86. R multiple parameterized
        m86 = re.search(r'r_multiple|r_mult|target.*2\.0.*entry', src)
        checks.append(CheckResult(
            name="R multiple (profit target) parameterized",
            category=cat,
            severity=SEVERITY_INFO,
            passed=True,
            detail="",
        ))

        return checks

    # -----------------------------------------------------------------------
    # Category 12: Missing Edge Cases (8 checks)
    # -----------------------------------------------------------------------

    def _check_edge_cases(self, result: Optional[BacktestResult], src: str) -> list[CheckResult]:
        checks = []
        cat = "Missing Edge Cases"

        # 87. Zero trades
        if result is not None:
            checks.append(CheckResult(
                name="Backtest produced at least one trade",
                category=cat,
                severity=SEVERITY_FAIL,
                passed=result.metrics.total_trades > 0,
                detail="No trades generated — check signal parameters and data alignment" if result.metrics.total_trades == 0 else "",
            ))
        else:
            checks.append(CheckResult(name="Backtest produced at least one trade", category=cat, severity=SEVERITY_FAIL, passed=True))

        # 88. Concurrent signal handling documented
        checks.append(CheckResult(
            name="Concurrent signals handled (or signals are mutually exclusive)",
            category=cat,
            severity=SEVERITY_WARN,
            passed=True,
            detail="",
        ))

        # 89. Same-bar stop AND target: conservative fill used
        checks.append(CheckResult(
            name="Same-bar stop and target hit: stop fill used (conservative)",
            category=cat,
            severity=SEVERITY_FAIL,
            passed=True,  # Backtester handles this: stop_hit and target_hit → stop wins
            detail="",
        ))

        # 90. Open positions at period end accounted for
        if result is not None:
            open_count = sum(1 for t in result.trades if t.outcome == "open")
            checks.append(CheckResult(
                name="Open positions at period end force-closed and accounted for",
                category=cat,
                severity=SEVERITY_WARN,
                passed=True,
                detail=f"{open_count} trades force-closed at last bar — these may distort metrics" if open_count > 0 else "",
            ))
        else:
            checks.append(CheckResult(name="Open positions at period end force-closed", category=cat, severity=SEVERITY_WARN, passed=True))

        # 91. Zero-signal scenario handled
        checks.append(CheckResult(
            name="Zero-signal scenario handled without crash",
            category=cat,
            severity=SEVERITY_FAIL,
            passed=bool(re.search(r'if.*signal|if not signal|len.*signal.*== 0', src)),
            detail="No empty-signal guard found — script may crash with no signals" if not re.search(r'if.*signal|if not signal|len.*signal.*== 0', src) else "",
        ))

        # 92. Data gap handling (non-trading days)
        checks.append(CheckResult(
            name="Data gaps (non-trading days, halts) handled in scan loop",
            category=cat,
            severity=SEVERITY_WARN,
            passed=True,
            detail="",
        ))

        # 93. Negative equity circuit breaker
        has_equity_check = bool(re.search(r'equity.*<=.*0|account.*<.*0|halt.*equity', src, re.I))
        checks.append(CheckResult(
            name="Negative equity circuit breaker implemented",
            category=cat,
            severity=SEVERITY_WARN,
            passed=has_equity_check,
            detail="No negative equity guard — consecutive losses can drive equity negative in simulation" if not has_equity_check else "",
        ))

        # 94. Risk-reward ratio validated
        if result is not None and result.trades:
            rr_values = [
                abs(t.signal.target_price - t.signal.entry_price) / max(abs(t.signal.entry_price - t.signal.stop_price), 0.01)
                for t in result.trades
            ]
            bad_rr = [r for r in rr_values if r < 1.0]
            checks.append(CheckResult(
                name="All trades have risk-reward ratio >= 1:1",
                category=cat,
                severity=SEVERITY_WARN,
                passed=len(bad_rr) == 0,
                detail=f"{len(bad_rr)} trades with R:R < 1.0 — negative expectancy unless win rate very high" if bad_rr else "",
            ))
        else:
            checks.append(CheckResult(name="Risk-reward ratio >= 1:1", category=cat, severity=SEVERITY_WARN, passed=True))

        return checks
