"""Discord bot setup for SPY/SPX options analysis employee.

Creates the SpyBot class with:
    - Shared DataManager instance (created once, used across all cogs)
    - Shared Store instance for persistence and cooldowns
    - Cog loading for analysis, scheduler, and alerts
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

        # Load cogs
        cog_extensions = [
            "src.discord_bot.cog_analysis",
            "src.discord_bot.cog_scheduler",
            "src.discord_bot.cog_alerts",
            "src.discord_bot.cog_webhooks",
            "src.discord_bot.cog_cheddarflow",
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

        # Clean up old database entries
        if self.store is not None:
            try:
                await self.store.cleanup_old()
                logger.info("Store cleanup complete")
            except Exception as exc:
                logger.error("Error during store cleanup: %s", exc)

        await super().close()
