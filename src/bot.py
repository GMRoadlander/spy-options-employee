"""Discord bot setup for SPY/SPX options analysis employee.

Creates the SpyBot class with:
    - Shared DataManager instance (created once, used across all cogs)
    - Shared Store instance for persistence and cooldowns
    - Cog loading for analysis, scheduler, and alerts
    - ML component initialization (Phase 3) with graceful degradation
    - Slash command tree syncing
"""

import logging

import discord
from discord.ext import commands

from src.data.data_manager import DataManager
from src.services import ServiceRegistry

logger = logging.getLogger(__name__)


class SpyBot(commands.Bot):
    """Discord bot for SPY/SPX options analysis.

    Attributes:
        services: Typed registry of all application services.
    """

    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

        # Typed service registry — cogs access this instead of getattr(self, ...)
        self.services = ServiceRegistry()

        # Legacy aliases — kept during migration so existing code doesn't break.
        # TODO: remove once all cogs use self.services directly.
        self.data_manager: DataManager = None  # type: ignore[assignment]
        self.store = None
        self.historical_store = None
        self.strategy_manager = None
        self.signal_logger = None
        self.strategy_parser = None
        self.hypothesis_manager = None
        self.paper_engine = None
        self.portfolio_analyzer = None
        self.feature_store = None
        self.regime_manager = None
        self.vol_manager = None
        self.sentiment_manager = None
        self.anomaly_manager = None
        self.flow_analyzer = None
        self.reasoning_engine = None
        self.reasoning_manager = None
        self.learning_manager = None

    async def setup_hook(self) -> None:
        """Initialize shared resources and load all cogs.

        This runs once before the bot starts processing events.
        """
        # Initialize the shared DataManager
        self.data_manager = DataManager()
        logger.info("DataManager initialized and shared across cogs")

        # Initialize the Store for persistence and cooldowns
        try:
            from src.db.store import Store
            self.store = Store()
            await self.store.init()
            logger.info("Store initialized (SQLite database ready)")
        except ImportError:
            logger.warning("Store module not available -- running without persistence")
            self.store = None
        except Exception as exc:
            logger.error("Store initialization failed: %s -- running without persistence", exc)
            self.store = None

        # Initialize HistoricalStore (Phase 2)
        try:
            from src.data.historical_store import HistoricalStore
            from src.config import config
            self.historical_store = HistoricalStore(config.historical_data_dir)
            logger.info("HistoricalStore initialized at %s", config.historical_data_dir)
        except ImportError:
            logger.warning("HistoricalStore module not available")
        except Exception as exc:
            logger.error("HistoricalStore initialization failed: %s", exc)

        # Initialize StrategyManager (Phase 2)
        if self.store is not None and hasattr(self.store, "_db") and self.store.connection is not None:
            try:
                from src.strategy.lifecycle import StrategyManager
                self.strategy_manager = StrategyManager(self.store.connection)
                await self.strategy_manager.init_tables()
                logger.info("StrategyManager initialized")
            except ImportError:
                logger.warning("StrategyManager module not available")
            except Exception as exc:
                logger.error("StrategyManager initialization failed: %s", exc)

        # Initialize SignalLogger (Phase 2)
        if self.store is not None and hasattr(self.store, "_db") and self.store.connection is not None:
            try:
                from src.db.signal_log import SignalLogger
                self.signal_logger = SignalLogger(self.store.connection)
                await self.signal_logger.init_table()
                logger.info("SignalLogger initialized")
            except ImportError:
                logger.warning("SignalLogger module not available")
            except Exception as exc:
                logger.error("SignalLogger initialization failed: %s", exc)

        # Initialize StrategyParser (Phase 2-3)
        try:
            from src.ai.strategy_parser import StrategyParser
            self.strategy_parser = StrategyParser()
            logger.info("StrategyParser initialized")
        except ImportError:
            logger.warning("StrategyParser module not available")
        except Exception as exc:
            logger.error("StrategyParser initialization failed: %s", exc)

        # Initialize HypothesisManager (Phase 2-3)
        if self.store is not None and hasattr(self.store, "_db") and self.store.connection is not None:
            try:
                from src.strategy.hypothesis import HypothesisManager
                self.hypothesis_manager = HypothesisManager(self.store.connection)
                await self.hypothesis_manager.init_tables()
                logger.info("HypothesisManager initialized")
            except ImportError:
                logger.warning("HypothesisManager module not available")
            except Exception as exc:
                logger.error("HypothesisManager initialization failed: %s", exc)

        # -- Phase 3: ML Intelligence Layer initialization --------------------
        # Each component is optional -- bot runs without any ML components.
        await self._init_ml_components()

        # -- Phase 4: Paper Trading Engine initialization ----------------------
        await self._init_paper_trading()

        # Sync all initialized services into the typed registry
        self._sync_services()

        # Log Phase 4 summary
        paper_components = {
            "PaperTradingEngine": self.paper_engine is not None,
            "PortfolioAnalyzer": self.portfolio_analyzer is not None,
        }
        paper_active = [k for k, v in paper_components.items() if v]
        logger.info(
            "Paper trading initialization: %d/%d active [%s]",
            len(paper_active),
            len(paper_components),
            ", ".join(paper_active) if paper_active else "none",
        )

        # Load cogs
        cog_extensions = [
            "src.discord_bot.cog_analysis",
            "src.discord_bot.cog_scheduler",
            "src.discord_bot.cog_alerts",
            "src.discord_bot.cog_webhooks",
            "src.discord_bot.cog_cheddarflow",
            "src.discord_bot.cog_strategy",
            "src.discord_bot.cog_journal",
            "src.discord_bot.cog_ml",
            "src.discord_bot.cog_paper",
        ]

        for ext in cog_extensions:
            try:
                await self.load_extension(ext)
                logger.info("Loaded extension: %s", ext)
            except Exception as exc:
                logger.error("Failed to load extension %s: %s", ext, exc, exc_info=True)

        # Slash command sync happens in on_ready() where guilds are available

    def _sync_services(self) -> None:
        """Copy all initialized components into the typed ServiceRegistry."""
        s = self.services
        s.data_manager = self.data_manager
        s.store = self.store
        s.historical_store = self.historical_store
        s.strategy_manager = self.strategy_manager
        s.signal_logger = self.signal_logger
        s.strategy_parser = self.strategy_parser
        s.hypothesis_manager = self.hypothesis_manager
        s.feature_store = self.feature_store
        s.regime_manager = self.regime_manager
        s.vol_manager = self.vol_manager
        s.sentiment_manager = self.sentiment_manager
        s.anomaly_manager = self.anomaly_manager
        s.flow_analyzer = self.flow_analyzer
        s.reasoning_engine = self.reasoning_engine
        s.reasoning_manager = self.reasoning_manager
        s.learning_manager = self.learning_manager
        s.paper_engine = self.paper_engine
        s.portfolio_analyzer = self.portfolio_analyzer

    async def _init_paper_trading(self) -> None:
        """Initialize Phase 4 paper trading components with graceful degradation.

        Requires Store (for database) and StrategyManager. Bot runs fine
        without paper trading if either is unavailable.
        """
        from src.config import config

        # Requires Store._db and StrategyManager
        if (
            self.store is None
            or not hasattr(self.store, "_db")
            or self.store.connection is None
        ):
            logger.warning("Paper trading skipped -- Store not available")
            return

        if self.strategy_manager is None:
            logger.warning("Paper trading skipped -- StrategyManager not available")
            return

        db = self.store.connection

        # 1. Build PaperTradingConfig from global config
        try:
            from src.paper.models import PaperTradingConfig
            paper_config = PaperTradingConfig(
                starting_capital=config.paper_starting_capital,
                spx_multiplier=config.paper_spx_multiplier,
                fee_per_contract=config.paper_fee_per_contract,
                slippage_pct=config.paper_slippage_pct,
                max_order_age_ticks=config.paper_max_order_age_ticks,
            )
        except Exception as exc:
            logger.error("PaperTradingConfig creation failed: %s", exc)
            return

        # Validate config
        if paper_config.starting_capital <= 0:
            logger.error("PAPER_STARTING_CAPITAL must be positive, got %.2f", paper_config.starting_capital)
            return
        if paper_config.spx_multiplier <= 0:
            logger.error("SPX multiplier must be positive")
            return

        # 2. Create PaperTradingEngine
        try:
            from src.paper.engine import PaperTradingEngine
            self.paper_engine = PaperTradingEngine(
                db=db,
                strategy_manager=self.strategy_manager,
                config=paper_config,
            )
            await self.paper_engine.init_tables()
            logger.info(
                "PaperTradingEngine initialized (capital=$%.0f, fee=$%.2f/contract)",
                paper_config.starting_capital,
                paper_config.fee_per_contract,
            )
        except ImportError:
            logger.warning("PaperTradingEngine module not available")
        except Exception as exc:
            logger.error("PaperTradingEngine initialization failed: %s", exc)
            self.paper_engine = None

        # 3. Wire signal logger to engine (for Bayesian calibration)
        if self.paper_engine is not None and self.signal_logger is not None:
            self.paper_engine._signal_logger = self.signal_logger

        # 4. Create PortfolioAnalyzer (sub-plan 4-5)
        if self.paper_engine is not None:
            try:
                from src.risk.analyzer import PortfolioAnalyzer
                from src.risk.config import RiskConfig
                risk_config = RiskConfig(
                    risk_free_rate=config.risk_free_rate,
                )
                self.portfolio_analyzer = PortfolioAnalyzer(config=risk_config)
                logger.info("PortfolioAnalyzer initialized")
            except ImportError:
                logger.warning("PortfolioAnalyzer module not available")
            except Exception as exc:
                logger.error("PortfolioAnalyzer initialization failed: %s", exc)

    async def _init_ml_components(self) -> None:
        """Initialize Phase 3 ML components with graceful degradation.

        Each component is wrapped in try/except so that a failure in one
        does not prevent others from initializing.  The bot runs fine
        without any ML components -- slash commands will show friendly
        "not initialized" messages.
        """
        from src.config import config

        # 1. FeatureStore (requires Store)
        if self.store is not None:
            try:
                from src.ml.feature_store import FeatureStore
                self.feature_store = FeatureStore(self.store)
                logger.info("FeatureStore initialized")
            except ImportError:
                logger.warning("FeatureStore module not available")
            except Exception as exc:
                logger.error("FeatureStore initialization failed: %s", exc)

        # 2. RegimeManager (if model checkpoint exists, load it)
        if self.feature_store is not None:
            try:
                from src.ml.regime import RegimeManager
                self.regime_manager = RegimeManager(
                    self.feature_store, config.ml_features_dir,
                )
                logger.info("RegimeManager initialized")
            except ImportError:
                logger.warning("RegimeManager module not available")
            except Exception as exc:
                logger.error("RegimeManager initialization failed: %s", exc)

        # 3. VolManager (if model checkpoint exists, load it)
        if self.feature_store is not None:
            try:
                from src.ml.volatility import VolManager
                self.vol_manager = VolManager(
                    self.feature_store, config.ml_features_dir,
                )
                logger.info("VolManager initialized")
            except ImportError:
                logger.warning("VolManager module not available")
            except Exception as exc:
                logger.error("VolManager initialization failed: %s", exc)

        # 4. SentimentScorer + SentimentManager (lazy FinBERT loading)
        if self.feature_store is not None:
            try:
                from src.ml.sentiment import SentimentScorer, SentimentManager
                scorer = SentimentScorer()  # Lazy -- won't load FinBERT until first use

                # NewsClient requires polygon_api_key
                news_client = None
                if config.polygon_api_key:
                    try:
                        from src.data.news_client import NewsClient
                        news_client = NewsClient(
                            api_key=config.polygon_api_key,
                            rate_limit=config.polygon_rate_limit,
                        )
                    except ImportError:
                        logger.warning("NewsClient module not available")

                if news_client is not None:
                    self.sentiment_manager = SentimentManager(
                        scorer, news_client, self.feature_store,
                    )
                    logger.info("SentimentManager initialized")
                else:
                    logger.warning("SentimentManager skipped -- no news client (needs POLYGON_API_KEY)")
            except ImportError:
                logger.warning("Sentiment modules not available")
            except Exception as exc:
                logger.error("SentimentManager initialization failed: %s", exc)

        # 5. AnomalyManager
        if self.feature_store is not None:
            try:
                from src.ml.anomaly import AnomalyManager
                self.anomaly_manager = AnomalyManager(
                    self.feature_store, config.ml_features_dir,
                )
                logger.info("AnomalyManager initialized")
            except ImportError:
                logger.warning("AnomalyManager module not available")
            except Exception as exc:
                logger.error("AnomalyManager initialization failed: %s", exc)

        # 6. FlowAnalyzer (requires polygon/UW API keys)
        try:
            from src.ml.anomaly import FlowAnalyzer

            uw_client = None
            if config.unusual_whales_api_key:
                try:
                    from src.data.unusual_whales_client import UnusualWhalesClient
                    uw_client = UnusualWhalesClient(api_key=config.unusual_whales_api_key)
                except ImportError:
                    logger.warning("UnusualWhalesClient module not available")

            self.flow_analyzer = FlowAnalyzer(uw_client=uw_client)
            logger.info("FlowAnalyzer initialized (UW client: %s)", "yes" if uw_client else "no")
        except ImportError:
            logger.warning("FlowAnalyzer module not available")
        except Exception as exc:
            logger.error("FlowAnalyzer initialization failed: %s", exc)

        # 7. ReasoningEngine + ReasoningManager (requires claude_api_key)
        if self.feature_store is not None and config.claude_api_key:
            try:
                from src.ai.reasoning import ReasoningEngine, ReasoningManager
                self.reasoning_engine = ReasoningEngine(api_key=config.claude_api_key)
                self.reasoning_manager = ReasoningManager(
                    engine=self.reasoning_engine,
                    feature_store=self.feature_store,
                    regime_manager=self.regime_manager,
                    vol_manager=self.vol_manager,
                    sentiment_manager=self.sentiment_manager,
                    anomaly_manager=self.anomaly_manager,
                    flow_analyzer=self.flow_analyzer,
                )
                logger.info("ReasoningEngine + ReasoningManager initialized")
            except ImportError:
                logger.warning("Reasoning modules not available")
            except Exception as exc:
                logger.error("ReasoningManager initialization failed: %s", exc)
        else:
            if not config.claude_api_key:
                logger.warning("ReasoningEngine skipped -- no CLAUDE_API_KEY configured")

        # 8. LearningManager (requires SignalLogger + Store)
        if (
            self.signal_logger is not None
            and self.store is not None
            and hasattr(self.store, "_db")
            and self.store.connection is not None
        ):
            try:
                from src.ml.learning import LearningManager, SignalTracker
                tracker = SignalTracker(self.signal_logger)
                self.learning_manager = LearningManager(tracker, self.store.connection)
                logger.info("LearningManager initialized")
            except ImportError:
                logger.warning("LearningManager module not available")
            except Exception as exc:
                logger.error("LearningManager initialization failed: %s", exc)

        # Log summary of ML initialization
        ml_components = {
            "FeatureStore": self.feature_store is not None,
            "RegimeManager": self.regime_manager is not None,
            "VolManager": self.vol_manager is not None,
            "SentimentManager": self.sentiment_manager is not None,
            "AnomalyManager": self.anomaly_manager is not None,
            "FlowAnalyzer": self.flow_analyzer is not None,
            "ReasoningManager": self.reasoning_manager is not None,
            "LearningManager": self.learning_manager is not None,
        }
        active = [k for k, v in ml_components.items() if v]
        inactive = [k for k, v in ml_components.items() if not v]
        logger.info(
            "ML initialization complete: %d/%d active [%s] | inactive [%s]",
            len(active),
            len(ml_components),
            ", ".join(active) if active else "none",
            ", ".join(inactive) if inactive else "none",
        )

    async def on_ready(self) -> None:
        """Called when the bot has connected to Discord and is ready."""
        logger.info("Bot is ready!")
        logger.info("Logged in as %s (ID: %s)", self.user, self.user.id if self.user else "unknown")
        logger.info("Connected to %d guild(s)", len(self.guilds))

        # Sync slash commands per guild (instant, no 1-hour wait)
        try:
            for guild in self.guilds:
                self.tree.copy_global_to(guild=guild)
                synced = await self.tree.sync(guild=guild)
                logger.info("Synced %d slash commands to guild %s (%s)", len(synced), guild.name, guild.id)
        except Exception as exc:
            logger.error("Failed to sync slash commands: %s", exc, exc_info=True)

        # Set presence
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="SPY/SPX options flow",
        )
        await self.change_presence(activity=activity)

    async def close(self) -> None:
        """Clean up shared resources before shutting down."""
        logger.info("Bot shutting down -- cleaning up resources")

        # Close DataManager sessions
        if self.data_manager is not None:
            try:
                await self.data_manager.close()
                logger.info("DataManager closed")
            except Exception as exc:
                logger.error("Error closing DataManager: %s", exc)

        # Close ML HTTP clients (news, unusual whales)
        if self.sentiment_manager is not None:
            try:
                news_client = getattr(self.sentiment_manager, "_news_client", None)
                if news_client is not None and hasattr(news_client, "close"):
                    await news_client.close()
                    logger.info("NewsClient closed")
            except Exception as exc:
                logger.error("Error closing NewsClient: %s", exc)

        if self.flow_analyzer is not None:
            try:
                uw_client = getattr(self.flow_analyzer, "_uw_client", None)
                if uw_client is not None and hasattr(uw_client, "close"):
                    await uw_client.close()
                    logger.info("UnusualWhalesClient closed")
            except Exception as exc:
                logger.error("Error closing UnusualWhalesClient: %s", exc)

        # Close paper trading engine (release references)
        if self.paper_engine is not None:
            logger.info("Paper trading engine shutdown")
            self.paper_engine = None
            self.portfolio_analyzer = None

        # Clean up old database entries and close connection
        if self.store is not None:
            try:
                await self.store.cleanup_old()
                logger.info("Store cleanup complete")
            except Exception as exc:
                logger.error("Error during store cleanup: %s", exc)
            try:
                await self.store.close()
                logger.info("Store connection closed")
            except Exception as exc:
                logger.error("Error closing store: %s", exc)

        await super().close()
