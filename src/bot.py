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

logger = logging.getLogger(__name__)


class SpyBot(commands.Bot):
    """Discord bot for SPY/SPX options analysis.

    Attributes:
        data_manager: Shared DataManager instance for all cogs.
        store: Shared Store instance for persistence and cooldowns.
    """

    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

        # Shared resources -- initialized in setup_hook
        self.data_manager: DataManager = None  # type: ignore[assignment]
        self.store = None  # Optional: will be set if db module is available
        self.historical_store = None  # Optional: HistoricalStore (Phase 2)
        self.strategy_manager = None  # Optional: StrategyManager (Phase 2)
        self.signal_logger = None  # Optional: SignalLogger (Phase 2)
        self.strategy_parser = None  # Optional: StrategyParser (Phase 2-3)
        self.hypothesis_manager = None  # Optional: HypothesisManager (Phase 2-3)

        # ML Intelligence Layer (Phase 3) -- all optional, bot runs without them
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
        if self.store is not None and hasattr(self.store, "_db") and self.store._db is not None:
            try:
                from src.strategy.lifecycle import StrategyManager
                self.strategy_manager = StrategyManager(self.store._db)
                await self.strategy_manager.init_tables()
                logger.info("StrategyManager initialized")
            except ImportError:
                logger.warning("StrategyManager module not available")
            except Exception as exc:
                logger.error("StrategyManager initialization failed: %s", exc)

        # Initialize SignalLogger (Phase 2)
        if self.store is not None and hasattr(self.store, "_db") and self.store._db is not None:
            try:
                from src.db.signal_log import SignalLogger
                self.signal_logger = SignalLogger(self.store._db)
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
        if self.store is not None and hasattr(self.store, "_db") and self.store._db is not None:
            try:
                from src.strategy.hypothesis import HypothesisManager
                self.hypothesis_manager = HypothesisManager(self.store._db)
                await self.hypothesis_manager.init_tables()
                logger.info("HypothesisManager initialized")
            except ImportError:
                logger.warning("HypothesisManager module not available")
            except Exception as exc:
                logger.error("HypothesisManager initialization failed: %s", exc)

        # -- Phase 3: ML Intelligence Layer initialization --------------------
        # Each component is optional -- bot runs without any ML components.
        await self._init_ml_components()

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

        # Sync slash commands with Discord
        try:
            synced = await self.tree.sync()
            logger.info("Synced %d slash commands", len(synced))
        except Exception as exc:
            logger.error("Failed to sync slash commands: %s", exc, exc_info=True)

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
            and self.store._db is not None
        ):
            try:
                from src.ml.learning import LearningManager, SignalTracker
                tracker = SignalTracker(self.signal_logger)
                self.learning_manager = LearningManager(tracker, self.store._db)
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

        # Clean up old database entries
        if self.store is not None:
            try:
                await self.store.cleanup_old()
                logger.info("Store cleanup complete")
            except Exception as exc:
                logger.error("Error during store cleanup: %s", exc)

        await super().close()
