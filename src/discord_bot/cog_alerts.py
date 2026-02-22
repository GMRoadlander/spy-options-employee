"""Alerts cog -- smart alert system for significant market events.

Checks conditions after each analysis cycle and posts alerts to the alerts channel:
    - Gamma flip: Net GEX crosses zero
    - Squeeze signal: PCR < 0.3 + negative GEX
    - Max pain convergence: Price within 0.5% of max pain
    - Large OI shift: >10% change at a key strike vs previous snapshot

Uses cooldown logic from Store to prevent alert spam (30-min cooldown per alert type).
"""

import logging
from datetime import datetime
from typing import Optional

import discord
from discord.ext import commands

from src.analysis.analyzer import AnalysisResult
from src.config import config
from src.discord_bot.embeds import build_alert_embed, COLOR_BEARISH, COLOR_BULLISH, COLOR_NEUTRAL

logger = logging.getLogger(__name__)


class AlertsCog(commands.Cog, name="Alerts"):
    """Smart alerts for significant market positioning changes."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        # Track previous analysis for comparison (OI shift detection)
        self._previous_results: dict[str, AnalysisResult] = {}
        # Track previous net GEX sign for gamma flip detection
        self._previous_net_gex_sign: dict[str, int] = {}  # +1, -1, or 0
        logger.info("AlertsCog loaded")

    def _get_alerts_channel(self) -> discord.TextChannel | None:
        """Get the alerts channel from config."""
        if config.alerts_channel_id == 0:
            logger.warning("Alerts channel ID not configured")
            return None
        channel = self.bot.get_channel(config.alerts_channel_id)
        if channel is None:
            logger.warning("Alerts channel %d not found", config.alerts_channel_id)
            return None
        if not isinstance(channel, discord.TextChannel):
            logger.warning("Alerts channel %d is not a text channel", config.alerts_channel_id)
            return None
        return channel

    async def _get_store(self):
        """Get the Store instance from the bot, if available.

        Returns:
            Store instance or None.
        """
        store = getattr(self.bot, "store", None)
        return store

    async def _can_fire(self, alert_type: str) -> bool:
        """Check if an alert type is off cooldown.

        Args:
            alert_type: The alert type identifier (e.g., "gamma_flip_SPY").

        Returns:
            True if the alert can fire (cooldown expired or no store).
        """
        store = await self._get_store()
        if store is None:
            # No store available -- allow alerts but log warning
            logger.debug("No store available for cooldown check, allowing alert %s", alert_type)
            return True
        try:
            return await store.check_cooldown(alert_type)
        except Exception as exc:
            logger.error("Cooldown check failed for %s: %s", alert_type, exc)
            return True  # Allow alert on error

    async def _set_cooldown(self, alert_type: str) -> None:
        """Set cooldown for an alert type.

        Args:
            alert_type: The alert type identifier.
        """
        store = await self._get_store()
        if store is None:
            return
        try:
            await store.set_cooldown(alert_type, minutes=config.alert_cooldown_minutes)
        except Exception as exc:
            logger.error("Failed to set cooldown for %s: %s", alert_type, exc)

    async def _send_alert(self, embed: discord.Embed) -> None:
        """Send an alert embed to the alerts channel.

        Args:
            embed: The alert embed to send.
        """
        channel = self._get_alerts_channel()
        if channel is None:
            return
        try:
            await channel.send(embed=embed)
        except discord.HTTPException as exc:
            logger.error("Failed to send alert: %s", exc)

    async def _log_signal(self, signal_type: str, ticker: str, direction: str, strength: float, metadata: dict | None = None) -> None:
        """Log a signal event if signal_logger is available (non-blocking).

        Args:
            signal_type: Type of signal (e.g., "gamma_flip").
            ticker: Ticker symbol.
            direction: Signal direction ("bullish", "bearish", "neutral").
            strength: Signal strength (0.0-1.0).
            metadata: Optional additional data.
        """
        signal_logger = getattr(self.bot, "signal_logger", None)
        if signal_logger is None:
            return
        try:
            from src.db.signal_log import SignalEvent
            event = SignalEvent(
                signal_type=signal_type,
                ticker=ticker,
                direction=direction,
                strength=strength,
                source="cog_alerts",
                metadata=metadata or {},
            )
            await signal_logger.log_signal(event)
        except Exception as exc:
            logger.debug("Signal logging failed (non-critical): %s", exc)

    async def check_alerts(self, result: AnalysisResult) -> None:
        """Run all alert checks against a new analysis result.

        Called by the scheduler cog after each analysis cycle.

        Args:
            result: The latest analysis result for a ticker.
        """
        ticker = result.ticker
        logger.debug("Checking alerts for %s", ticker)

        await self._check_gamma_flip(result)
        await self._check_squeeze(result)
        await self._check_max_pain_convergence(result)
        await self._check_oi_shift(result)

        # Store current result for next comparison
        self._previous_results[ticker] = result

        # Store current net GEX sign
        if result.gex.net_gex > 0:
            self._previous_net_gex_sign[ticker] = 1
        elif result.gex.net_gex < 0:
            self._previous_net_gex_sign[ticker] = -1
        else:
            self._previous_net_gex_sign[ticker] = 0

    async def _check_gamma_flip(self, result: AnalysisResult) -> None:
        """Check if net GEX has crossed zero since last check.

        A gamma flip means dealers shifted from long gamma (dampening) to
        short gamma (amplifying), or vice versa. This is a significant event.

        Args:
            result: Current analysis result.
        """
        ticker = result.ticker
        alert_type = f"gamma_flip_{ticker}"

        # Determine current sign
        current_sign = 1 if result.gex.net_gex > 0 else (-1 if result.gex.net_gex < 0 else 0)
        previous_sign = self._previous_net_gex_sign.get(ticker)

        # No previous data -- can't detect a flip
        if previous_sign is None:
            return

        # Check if sign changed (and neither is zero)
        if previous_sign != 0 and current_sign != 0 and previous_sign != current_sign:
            if not await self._can_fire(alert_type):
                logger.debug("Gamma flip alert for %s on cooldown", ticker)
                return

            direction = "POSITIVE (dampening)" if current_sign > 0 else "NEGATIVE (amplifying)"
            prev_direction = "positive" if previous_sign > 0 else "negative"

            embed = build_alert_embed(
                alert_type="gamma_flip",
                ticker=ticker,
                title=f"Gamma Flip -- {ticker}",
                description=(
                    f"Net GEX has flipped from {prev_direction} to **{direction}**. "
                    f"Dealer hedging behavior has changed."
                ),
                fields={
                    "Net GEX": f"${result.gex.net_gex:,.0f}",
                    "Gamma Flip Level": f"${result.gex.gamma_flip:,.2f}" if result.gex.gamma_flip else "N/A",
                    "Spot Price": f"${result.spot_price:,.2f}",
                    "Squeeze Prob": f"{result.gex.squeeze_probability:.0%}",
                },
                color=COLOR_BULLISH if current_sign > 0 else COLOR_BEARISH,
            )

            await self._send_alert(embed)
            await self._set_cooldown(alert_type)
            await self._log_signal(
                "gamma_flip", ticker,
                "bullish" if current_sign > 0 else "bearish",
                0.8,
                {"net_gex": result.gex.net_gex, "direction": direction},
            )
            logger.info("ALERT: Gamma flip for %s -> %s", ticker, direction)

    async def _check_squeeze(self, result: AnalysisResult) -> None:
        """Check for squeeze conditions: PCR < threshold + negative GEX.

        A squeeze alert fires when extreme call buying (low PCR) combines
        with negative GEX (dealers short gamma), creating conditions for
        an explosive upward move.

        Args:
            result: Current analysis result.
        """
        ticker = result.ticker
        alert_type = f"squeeze_{ticker}"

        pcr_threshold = config.squeeze_pcr_threshold
        is_squeeze = (
            result.pcr.volume_pcr < pcr_threshold
            and result.gex.net_gex < 0
        )

        if not is_squeeze:
            return

        if not await self._can_fire(alert_type):
            logger.debug("Squeeze alert for %s on cooldown", ticker)
            return

        embed = build_alert_embed(
            alert_type="squeeze",
            ticker=ticker,
            title=f"SQUEEZE ALERT -- {ticker}",
            description=(
                f"Extreme call buying (PCR {result.pcr.volume_pcr:.3f} < {pcr_threshold}) "
                f"combined with negative GEX. Dealers are short gamma and must buy into rallies. "
                f"Conditions favor an explosive upward squeeze."
            ),
            fields={
                "Volume PCR": f"{result.pcr.volume_pcr:.3f}",
                "Net GEX": f"${result.gex.net_gex:,.0f}",
                "Squeeze Prob": f"{result.gex.squeeze_probability:.0%}",
                "Spot Price": f"${result.spot_price:,.2f}",
                "Dealer Position": result.pcr.dealer_positioning.replace("_", " ").title(),
                "PCR Signal": result.pcr.signal.replace("_", " ").title(),
            },
            color=COLOR_BULLISH,
        )

        await self._send_alert(embed)
        await self._set_cooldown(alert_type)
        await self._log_signal(
            "squeeze", ticker, "bullish", 0.9,
            {"volume_pcr": result.pcr.volume_pcr, "net_gex": result.gex.net_gex},
        )
        logger.info("ALERT: Squeeze signal for %s (PCR=%.3f, GEX=%.0f)", ticker, result.pcr.volume_pcr, result.gex.net_gex)

    async def _check_max_pain_convergence(self, result: AnalysisResult) -> None:
        """Check if current price is converging on max pain.

        When price is within convergence_pct of max pain, the "expiry magnet"
        effect is in play and price movement may stall.

        Args:
            result: Current analysis result.
        """
        ticker = result.ticker
        alert_type = f"max_pain_convergence_{ticker}"

        convergence_pct = config.max_pain_convergence_pct
        abs_distance = abs(result.max_pain.distance_pct) / 100.0  # Convert from pct to decimal

        if abs_distance > convergence_pct:
            return

        if not await self._can_fire(alert_type):
            logger.debug("Max pain convergence alert for %s on cooldown", ticker)
            return

        embed = build_alert_embed(
            alert_type="max_pain_convergence",
            ticker=ticker,
            title=f"Max Pain Convergence -- {ticker}",
            description=(
                f"Price ({result.spot_price:,.2f}) is within "
                f"{abs_distance * 100:.2f}% of max pain ({result.max_pain.max_pain_price:,.2f}). "
                f"Expiry magnet effect may limit further movement."
            ),
            fields={
                "Max Pain": f"${result.max_pain.max_pain_price:,.2f}",
                "Spot Price": f"${result.spot_price:,.2f}",
                "Distance": f"{result.max_pain.distance_pct:+.2f}%",
                "Expiry": str(result.max_pain.expiry),
            },
            color=COLOR_NEUTRAL,
        )

        await self._send_alert(embed)
        await self._set_cooldown(alert_type)
        await self._log_signal(
            "max_pain_convergence", ticker, "neutral", 0.6,
            {"spot": result.spot_price, "max_pain": result.max_pain.max_pain_price, "distance_pct": result.max_pain.distance_pct},
        )
        logger.info(
            "ALERT: Max pain convergence for %s (spot=%.2f, mp=%.2f, dist=%.3f%%)",
            ticker,
            result.spot_price,
            result.max_pain.max_pain_price,
            result.max_pain.distance_pct,
        )

    async def _check_oi_shift(self, result: AnalysisResult) -> None:
        """Check for large OI shifts at key strikes compared to previous snapshot.

        Compares current vs previous OI at key levels identified by strike intel.
        If OI changes by more than the threshold percentage, an alert fires.

        Args:
            result: Current analysis result.
        """
        ticker = result.ticker
        alert_type = f"oi_shift_{ticker}"

        previous = self._previous_results.get(ticker)
        if previous is None:
            return  # Need a previous snapshot to compare

        threshold_pct = config.oi_shift_threshold_pct

        # Compare OI at key levels
        # Build a map of strike -> (call_oi, put_oi) for current and previous
        current_oi = self._extract_key_strike_oi(result)
        previous_oi = self._extract_key_strike_oi(previous)

        shifts: list[str] = []
        for strike, (curr_call, curr_put) in current_oi.items():
            if strike not in previous_oi:
                continue

            prev_call, prev_put = previous_oi[strike]

            # Check call OI shift
            if prev_call > 0:
                call_change = abs(curr_call - prev_call) / prev_call
                if call_change > threshold_pct:
                    direction = "UP" if curr_call > prev_call else "DOWN"
                    shifts.append(
                        f"Call ${strike:.0f}: {prev_call:,} -> {curr_call:,} ({direction} {call_change:.1%})"
                    )

            # Check put OI shift
            if prev_put > 0:
                put_change = abs(curr_put - prev_put) / prev_put
                if put_change > threshold_pct:
                    direction = "UP" if curr_put > prev_put else "DOWN"
                    shifts.append(
                        f"Put ${strike:.0f}: {prev_put:,} -> {curr_put:,} ({direction} {put_change:.1%})"
                    )

        if not shifts:
            return

        if not await self._can_fire(alert_type):
            logger.debug("OI shift alert for %s on cooldown", ticker)
            return

        # Limit to top 6 shifts for embed readability
        shift_text = "\n".join(shifts[:6])
        if len(shifts) > 6:
            shift_text += f"\n... and {len(shifts) - 6} more"

        embed = build_alert_embed(
            alert_type="oi_shift",
            ticker=ticker,
            title=f"Large OI Shift -- {ticker}",
            description=(
                f"Significant open interest changes detected at key strikes "
                f"(>{threshold_pct:.0%} threshold)."
            ),
            fields={
                "Shifts Detected": str(len(shifts)),
                "Spot Price": f"${result.spot_price:,.2f}",
                "Details": shift_text,
            },
            color=COLOR_NEUTRAL,
        )

        await self._send_alert(embed)
        await self._set_cooldown(alert_type)
        await self._log_signal(
            "oi_shift", ticker, "neutral", 0.5,
            {"shifts_count": len(shifts), "shifts": shifts[:6]},
        )
        logger.info("ALERT: OI shift for %s (%d shifts detected)", ticker, len(shifts))

    @staticmethod
    def _extract_key_strike_oi(result: AnalysisResult) -> dict[float, tuple[int, int]]:
        """Extract OI at key strike levels from an analysis result.

        Uses the key_levels from strike_intel to identify which strikes to monitor,
        then reconstructs approximate OI from PCR totals and GEX data.

        For a proper implementation, this would need per-strike OI data from the chain.
        Since we only have aggregate PCR data, we use the GEX strike data as a proxy --
        strikes with higher absolute GEX generally correspond to higher OI.

        Args:
            result: Analysis result with strike intel and GEX data.

        Returns:
            Dict mapping strike price to (call_oi_proxy, put_oi_proxy).
        """
        oi_map: dict[float, tuple[int, int]] = {}

        gex = result.gex
        if not gex.strikes:
            return oi_map

        # Use absolute GEX values as OI proxies at each strike
        for i, strike in enumerate(gex.strikes):
            call_gex = abs(gex.call_gex[i]) if i < len(gex.call_gex) else 0.0
            put_gex = abs(gex.put_gex[i]) if i < len(gex.put_gex) else 0.0
            # Normalize to integer "OI proxy" values
            oi_map[strike] = (int(call_gex), int(put_gex))

        return oi_map


async def setup(bot: commands.Bot) -> None:
    """Register the AlertsCog with the bot."""
    await bot.add_cog(AlertsCog(bot))
    logger.info("AlertsCog registered")
