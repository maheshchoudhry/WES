"""Budget management (Sprint 11).

The founder configures daily/monthly spend limits, a per-run max cost/tokens, a
warning threshold, and whether to hard-stop. The orchestration layer calls
``check`` before each execution; when a hard stop is breached the run is refused
before any provider is contacted.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.provider_platform import BudgetConfig, ProviderUsage


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _month() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


class BudgetExceededError(Exception):
    """Raised when a hard-stop budget limit would be breached."""


@dataclass
class BudgetDecision:
    allowed: bool
    reason: str | None
    warning: bool
    daily_spent: float
    monthly_spent: float


class BudgetService:
    def __init__(self, db: Session):
        self.db = db

    # -- config ------------------------------------------------------------

    def get_config(self) -> BudgetConfig:
        cfg = self.db.scalar(select(BudgetConfig).where(BudgetConfig.scope == "global"))
        if cfg is None:
            cfg = BudgetConfig(scope="global")
            self.db.add(cfg)
            self.db.flush()
        return cfg

    def update_config(self, **fields) -> BudgetConfig:
        cfg = self.get_config()
        for key, value in fields.items():
            if value is not None and hasattr(cfg, key):
                setattr(cfg, key, value)
        self.db.flush()
        return cfg

    def serialize(self, cfg: BudgetConfig) -> dict:
        return {
            "daily_cost_limit": cfg.daily_cost_limit,
            "monthly_cost_limit": cfg.monthly_cost_limit,
            "max_cost": cfg.max_cost,
            "max_tokens": cfg.max_tokens,
            "warning_threshold": cfg.warning_threshold,
            "hard_stop": cfg.hard_stop,
            "currency": cfg.currency,
        }

    # -- spend -------------------------------------------------------------

    def _spend(self, period_col, key: str) -> float:
        return (
            self.db.scalar(
                select(func.coalesce(func.sum(ProviderUsage.estimated_cost), 0.0)).where(
                    period_col == key
                )
            )
            or 0.0
        )

    def daily_spend(self) -> float:
        return self._spend(ProviderUsage.day, _today())

    def monthly_spend(self) -> float:
        return self._spend(ProviderUsage.month, _month())

    def status(self) -> dict:
        cfg = self.get_config()
        daily, monthly = self.daily_spend(), self.monthly_spend()
        thr = cfg.warning_threshold or 0.8

        def pct(spent, limit):
            return round(spent / limit, 3) if limit else 0.0

        daily_pct = pct(daily, cfg.daily_cost_limit)
        monthly_pct = pct(monthly, cfg.monthly_cost_limit)
        warning = (cfg.daily_cost_limit and daily_pct >= thr) or (
            cfg.monthly_cost_limit and monthly_pct >= thr
        )
        exceeded = (cfg.daily_cost_limit and daily >= cfg.daily_cost_limit) or (
            cfg.monthly_cost_limit and monthly >= cfg.monthly_cost_limit
        )
        return {
            "config": self.serialize(cfg),
            "daily_spent": round(daily, 6),
            "monthly_spent": round(monthly, 6),
            "daily_pct": daily_pct,
            "monthly_pct": monthly_pct,
            "warning": bool(warning),
            "exceeded": bool(exceeded),
            "hard_stop_active": bool(exceeded and cfg.hard_stop),
        }

    # -- pre-execution check ----------------------------------------------

    def check(self, estimated_cost: float = 0.0, estimated_tokens: int = 0) -> BudgetDecision:
        cfg = self.get_config()
        daily, monthly = self.daily_spend(), self.monthly_spend()
        thr = cfg.warning_threshold or 0.8

        reason = None
        # Per-run caps.
        if cfg.max_cost is not None and estimated_cost > cfg.max_cost:
            reason = f"Estimated cost {estimated_cost:.4f} exceeds per-run max {cfg.max_cost}"
        if cfg.max_tokens is not None and estimated_tokens > cfg.max_tokens:
            reason = f"Estimated tokens {estimated_tokens} exceed per-run max {cfg.max_tokens}"
        # Period caps (projected).
        if cfg.daily_cost_limit is not None and (daily + estimated_cost) > cfg.daily_cost_limit:
            reason = f"Daily budget {cfg.daily_cost_limit} would be exceeded"
        if (
            cfg.monthly_cost_limit is not None
            and (monthly + estimated_cost) > cfg.monthly_cost_limit
        ):
            reason = f"Monthly budget {cfg.monthly_cost_limit} would be exceeded"

        allowed = reason is None or not cfg.hard_stop
        warning = False
        if cfg.daily_cost_limit:
            warning = warning or (daily + estimated_cost) / cfg.daily_cost_limit >= thr
        if cfg.monthly_cost_limit:
            warning = warning or (monthly + estimated_cost) / cfg.monthly_cost_limit >= thr
        return BudgetDecision(
            allowed=allowed,
            reason=reason,
            warning=bool(warning),
            daily_spent=round(daily, 6),
            monthly_spent=round(monthly, 6),
        )
