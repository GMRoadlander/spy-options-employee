"""Typed service registry for dependency injection.

Replaces the SpyBot god-object pattern where cogs fish out dependencies
via ``getattr(self.bot, "manager_name", None)``.  All services are
optional except ``data_manager``; cogs that need a service access it as
a typed attribute rather than an untyped string lookup.

Usage in cogs::

    class MyCog(commands.Cog):
        def __init__(self, bot: commands.Bot) -> None:
            self.bot = bot
            self.services: ServiceRegistry = bot.services  # type: ignore[attr-defined]

        @app_commands.command()
        async def my_command(self, interaction):
            if self.services.paper_engine is None:
                await interaction.response.send_message("Paper trading not available")
                return
            ...
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.ai.reasoning import ReasoningEngine, ReasoningManager
    from src.ai.strategy_parser import StrategyParser
    from src.data.data_manager import DataManager
    from src.data.historical_store import HistoricalStore
    from src.db.signal_log import SignalLogger
    from src.db.store import Store
    from src.ml.anomaly import AnomalyManager
    from src.ml.feature_store import FeatureStore
    from src.ml.learning import LearningManager
    from src.ml.regime import RegimeManager
    from src.ml.sentiment import SentimentManager
    from src.ml.volatility import VolManager
    from src.paper.engine import PaperTradingEngine
    from src.paper.portfolio import PortfolioAnalyzer
    from src.strategy.hypothesis import HypothesisManager
    from src.strategy.lifecycle import StrategyManager


@dataclass
class ServiceRegistry:
    """Central registry of all application services.

    Every service except ``data_manager`` defaults to ``None`` and is
    populated during bot startup.  Cogs read these attributes directly
    instead of using ``getattr(self.bot, ...)``.
    """

    # Phase 1 — Core (required)
    data_manager: DataManager | None = None

    # Phase 1 — Persistence (optional)
    store: Store | None = None
    historical_store: HistoricalStore | None = None

    # Phase 2 — Strategy (optional, require store)
    strategy_manager: StrategyManager | None = None
    signal_logger: SignalLogger | None = None
    strategy_parser: StrategyParser | None = None
    hypothesis_manager: HypothesisManager | None = None

    # Phase 3 — ML Intelligence (all optional)
    feature_store: FeatureStore | None = None
    regime_manager: RegimeManager | None = None
    vol_manager: VolManager | None = None
    sentiment_manager: SentimentManager | None = None
    anomaly_manager: AnomalyManager | None = None
    flow_analyzer: Any | None = None  # FlowAnalyzer (optional dep)
    reasoning_engine: ReasoningEngine | None = None
    reasoning_manager: ReasoningManager | None = None
    learning_manager: LearningManager | None = None

    # Phase 4 — Paper Trading (optional, require store + strategy_manager)
    paper_engine: PaperTradingEngine | None = None
    portfolio_analyzer: PortfolioAnalyzer | None = None
