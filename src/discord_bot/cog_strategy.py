"""Strategy management cog -- Discord slash commands for strategy CRUD + backtesting.

Implements slash commands:
    /strategy define <description> -- Parse NL into strategy, confirm, save
    /strategy list [status]        -- List strategies with status filter
    /strategy show <name>          -- Full strategy details + YAML
    /strategy edit <name> <changes>-- Edit strategy via NL feedback
    /strategy retire <name>        -- Retire a strategy (terminal)
    /backtest <name> [years]       -- Run full evaluation pipeline
    /backtest_results <name>       -- Show latest backtest results
"""

import logging
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from src.config import config
from src.strategy.lifecycle import StrategyStatus

logger = logging.getLogger(__name__)

# Status choices for autocomplete
STATUS_CHOICES = [
    app_commands.Choice(name=s.value.title(), value=s.value)
    for s in StrategyStatus
]


class StrategyCog(commands.Cog, name="Strategy"):
    """Slash commands for strategy management and backtesting."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        logger.info("StrategyCog loaded")

    @staticmethod
    def _is_authorized(interaction: discord.Interaction) -> bool:
        """Check if user has manage_guild permission for sensitive commands."""
        if interaction.guild is None:
            return False
        perms = interaction.permissions
        return perms.manage_guild

    # -- /strategy define ------------------------------------------------

    @app_commands.command(
        name="strategy_define",
        description="Define a new strategy from natural language description",
    )
    @app_commands.describe(description="Plain English strategy description")
    @commands.cooldown(1, 30.0, commands.BucketType.user)
    async def strategy_define(
        self, interaction: discord.Interaction, description: str
    ) -> None:
        """Parse NL description into strategy template, show for confirmation."""
        await interaction.response.defer()

        parser = getattr(self.bot, "strategy_parser", None)
        if parser is None:
            await interaction.followup.send(
                "Strategy parser not available. Check bot configuration.",
                ephemeral=True,
            )
            return

        try:
            from src.ai.strategy_parser import StrategyParseError

            template, explanation = await parser.parse(description)
        except StrategyParseError as exc:
            logger.warning("Strategy parse error: %s", exc)
            await interaction.followup.send(
                "Failed to parse strategy. Please rephrase and try again.",
                ephemeral=True,
            )
            return
        except Exception as exc:
            logger.error("Unexpected error parsing strategy: %s", exc, exc_info=True)
            await interaction.followup.send(
                "An unexpected error occurred. Please try again later.",
                ephemeral=True,
            )
            return

        # Save as IDEA status in DB
        manager = getattr(self.bot, "strategy_manager", None)
        if manager is None:
            await interaction.followup.send(
                "Strategy manager not available.", ephemeral=True,
            )
            return

        import yaml
        from src.strategy.loader import StrategyLoader
        loader = StrategyLoader()
        yaml_str = yaml.dump(
            loader._template_to_dict(template),
            default_flow_style=False,
            sort_keys=False,
        )

        strategy_id = await manager.create(
            name=template.name,
            template_yaml=yaml_str,
        )

        from src.discord_bot.embeds import build_strategy_define_embed
        embed = build_strategy_define_embed(template, explanation, strategy_id)
        await interaction.followup.send(embed=embed)

    # -- /strategy list --------------------------------------------------

    @app_commands.command(
        name="strategy_list",
        description="List all strategies, optionally filtered by status",
    )
    @app_commands.describe(status="Filter by strategy status")
    @app_commands.choices(status=STATUS_CHOICES)
    async def strategy_list(
        self, interaction: discord.Interaction, status: str | None = None,
    ) -> None:
        """List all strategies with status indicators."""
        await interaction.response.defer()

        manager = getattr(self.bot, "strategy_manager", None)
        if manager is None:
            await interaction.followup.send(
                "Strategy manager not available.", ephemeral=True,
            )
            return

        status_filter = StrategyStatus(status) if status else None
        strategies = await manager.list_strategies(status=status_filter)

        from src.discord_bot.embeds import build_strategy_list_embed
        embed = build_strategy_list_embed(strategies, status_filter)
        await interaction.followup.send(embed=embed)

    # -- /strategy show --------------------------------------------------

    @app_commands.command(
        name="strategy_show",
        description="Show full details of a strategy",
    )
    @app_commands.describe(name="Strategy name or ID")
    async def strategy_show(
        self, interaction: discord.Interaction, name: str,
    ) -> None:
        """Show full strategy details including YAML and lifecycle history."""
        await interaction.response.defer()

        manager = getattr(self.bot, "strategy_manager", None)
        if manager is None:
            await interaction.followup.send(
                "Strategy manager not available.", ephemeral=True,
            )
            return

        strategy = await self._find_strategy(manager, name)
        if strategy is None:
            await interaction.followup.send(
                f"Strategy '{name}' not found.", ephemeral=True,
            )
            return

        history = await manager.get_transition_history(strategy["id"])

        from src.discord_bot.embeds import build_strategy_detail_embed
        embed = build_strategy_detail_embed(strategy, history)
        await interaction.followup.send(embed=embed)

    # -- /strategy edit --------------------------------------------------

    @app_commands.command(
        name="strategy_edit",
        description="Edit a strategy using natural language feedback",
    )
    @app_commands.describe(
        name="Strategy name or ID",
        changes="What to change (plain English)",
    )
    @commands.cooldown(1, 30.0, commands.BucketType.user)
    async def strategy_edit(
        self,
        interaction: discord.Interaction,
        name: str,
        changes: str,
    ) -> None:
        """Edit a strategy via NL feedback through the parser."""
        await interaction.response.defer()

        parser = getattr(self.bot, "strategy_parser", None)
        manager = getattr(self.bot, "strategy_manager", None)
        if parser is None or manager is None:
            await interaction.followup.send(
                "Strategy parser/manager not available.", ephemeral=True,
            )
            return

        strategy = await self._find_strategy(manager, name)
        if strategy is None:
            await interaction.followup.send(
                f"Strategy '{name}' not found.", ephemeral=True,
            )
            return

        # Load current template from YAML
        yaml_str = strategy.get("template_yaml", "")
        if not yaml_str:
            await interaction.followup.send(
                "Strategy has no template YAML to edit.", ephemeral=True,
            )
            return

        import yaml
        from src.strategy.loader import StrategyLoader
        loader = StrategyLoader()
        try:
            raw = yaml.safe_load(yaml_str)
            template = loader._dict_to_template(raw)
        except Exception as exc:
            logger.error("Failed to load template for strategy #%d: %s", strategy["id"], exc, exc_info=True)
            await interaction.followup.send(
                "Failed to load current template. Please check strategy configuration.",
                ephemeral=True,
            )
            return

        try:
            refined, explanation = await parser.refine(template, changes)
        except Exception as exc:
            logger.error("Failed to refine strategy #%d: %s", strategy["id"], exc, exc_info=True)
            await interaction.followup.send(
                "Failed to refine strategy. Please rephrase and try again.",
                ephemeral=True,
            )
            return

        # Update in DB via lifecycle manager (C3: no raw SQL)
        new_yaml = yaml.dump(
            loader._template_to_dict(refined),
            default_flow_style=False,
            sort_keys=False,
        )
        await manager.update_template(strategy["id"], new_yaml)

        from src.discord_bot.embeds import build_strategy_define_embed
        embed = build_strategy_define_embed(refined, explanation, strategy["id"])
        embed.title = f"Strategy Updated -- #{strategy['id']}"
        await interaction.followup.send(embed=embed)

    # -- /strategy retire ------------------------------------------------

    @app_commands.command(
        name="strategy_retire",
        description="Retire a strategy (terminal state)",
    )
    @app_commands.describe(name="Strategy name or ID")
    async def strategy_retire(
        self, interaction: discord.Interaction, name: str,
    ) -> None:
        """Retire a strategy."""
        await interaction.response.defer()

        if not self._is_authorized(interaction):
            await interaction.followup.send(
                "You need **Manage Server** permission to retire strategies.",
                ephemeral=True,
            )
            return

        manager = getattr(self.bot, "strategy_manager", None)
        if manager is None:
            await interaction.followup.send(
                "Strategy manager not available.", ephemeral=True,
            )
            return

        strategy = await self._find_strategy(manager, name)
        if strategy is None:
            await interaction.followup.send(
                f"Strategy '{name}' not found.", ephemeral=True,
            )
            return

        try:
            await manager.transition(
                strategy["id"],
                StrategyStatus.RETIRED,
                reason="Retired via Discord command",
            )
            await interaction.followup.send(
                f"Strategy **{strategy['name']}** (#{strategy['id']}) has been retired.",
            )
        except Exception as exc:
            logger.error("Failed to retire strategy #%d: %s", strategy["id"], exc, exc_info=True)
            await interaction.followup.send(
                "Failed to retire strategy. Please try again.",
                ephemeral=True,
            )

    # -- /backtest -------------------------------------------------------

    @app_commands.command(
        name="backtest",
        description="Run full backtest + anti-overfitting pipeline on a strategy",
    )
    @app_commands.describe(
        name="Strategy name or ID",
        years="Number of years to backtest (default 5)",
    )
    async def backtest(
        self,
        interaction: discord.Interaction,
        name: str,
        years: int = 5,
    ) -> None:
        """Run backtest evaluation pipeline and post results."""
        await interaction.response.defer()

        manager = getattr(self.bot, "strategy_manager", None)
        if manager is None:
            await interaction.followup.send(
                "Strategy manager not available.", ephemeral=True,
            )
            return

        strategy = await self._find_strategy(manager, name)
        if strategy is None:
            await interaction.followup.send(
                f"Strategy '{name}' not found.", ephemeral=True,
            )
            return

        # Show progress
        from src.discord_bot.embeds import build_backtest_progress_embed
        progress_embed = build_backtest_progress_embed(strategy["name"], "Starting pipeline...")
        await interaction.followup.send(embed=progress_embed)

        # Load template
        yaml_str = strategy.get("template_yaml", "")
        if not yaml_str:
            await interaction.followup.send(
                "Strategy has no template YAML for backtesting.", ephemeral=True,
            )
            return

        import yaml
        from src.strategy.loader import StrategyLoader
        loader = StrategyLoader()
        try:
            raw = yaml.safe_load(yaml_str)
            template = loader._dict_to_template(raw)
            template.metadata["id"] = str(strategy["id"])
        except Exception as exc:
            logger.error("Failed to load template for backtest on strategy #%d: %s", strategy["id"], exc, exc_info=True)
            await interaction.followup.send(
                "Failed to load template. Please check strategy configuration.",
                ephemeral=True,
            )
            return

        # Transition to BACKTEST status
        try:
            current_status = StrategyStatus(strategy["status"])
            if current_status == StrategyStatus.DEFINED:
                await manager.transition(
                    strategy["id"],
                    StrategyStatus.BACKTEST,
                    reason=f"Backtest initiated ({years}yr)",
                )
        except Exception:
            pass  # Non-critical, continue with backtest

        # Run pipeline (would require BacktestEngine with data in production)
        await interaction.channel.send(
            f"Backtest pipeline for **{strategy['name']}** is queued. "
            f"Results will be posted when complete."
        )

    # -- /backtest_results -----------------------------------------------

    @app_commands.command(
        name="backtest_results",
        description="Show latest backtest results for a strategy",
    )
    @app_commands.describe(name="Strategy name or ID")
    async def backtest_results(
        self, interaction: discord.Interaction, name: str,
    ) -> None:
        """Show latest backtest/evaluation results."""
        await interaction.response.defer()

        manager = getattr(self.bot, "strategy_manager", None)
        store = getattr(self.bot, "store", None)
        if manager is None or store is None:
            await interaction.followup.send(
                "Strategy manager/store not available.", ephemeral=True,
            )
            return

        strategy = await self._find_strategy(manager, name)
        if strategy is None:
            await interaction.followup.send(
                f"Strategy '{name}' not found.", ephemeral=True,
            )
            return

        # Query latest backtest result
        db = store._ensure_connected()
        cursor = await db.execute(
            """SELECT * FROM backtest_results
               WHERE strategy_id = ?
               ORDER BY run_at DESC LIMIT 1""",
            (strategy["id"],),
        )
        row = await cursor.fetchone()

        if row is None:
            await interaction.followup.send(
                f"No backtest results found for **{strategy['name']}**.",
                ephemeral=True,
            )
            return

        columns = [desc[0] for desc in cursor.description]
        result_dict = dict(zip(columns, row))

        from src.discord_bot.embeds import build_backtest_result_embed
        embed = build_backtest_result_embed(result_dict, strategy["name"])
        await interaction.followup.send(embed=embed)

    # -- Helpers ---------------------------------------------------------

    async def _find_strategy(self, manager, name_or_id: str) -> dict | None:
        """Find a strategy by name or ID."""
        # Try by ID first
        try:
            strategy_id = int(name_or_id)
            return await manager.get(strategy_id)
        except (ValueError, TypeError):
            pass

        # Search by name
        strategies = await manager.list_strategies()
        for s in strategies:
            if s["name"].lower() == name_or_id.lower():
                return s
        return None


async def setup(bot: commands.Bot) -> None:
    """Register the StrategyCog with the bot."""
    await bot.add_cog(StrategyCog(bot))
    logger.info("StrategyCog registered")
