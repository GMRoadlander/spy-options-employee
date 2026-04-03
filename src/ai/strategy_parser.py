"""Natural language strategy parser using Claude AI.

Converts Borey's plain-English strategy descriptions into validated
StrategyTemplate objects. Uses Claude Sonnet to parse natural language
into structured YAML, then validates the result against the schema.

Also supports iterative refinement: Borey can say "make the delta range
tighter" and the parser will modify the existing template accordingly.
"""

import asyncio
import logging
from typing import Any

import anthropic
import httpx
import yaml

from src.config import config
from src.strategy.loader import StrategyLoader
from src.strategy.schema import (
    StrategyTemplate,
    validate_strategy,
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are an options strategy parser. Convert plain English strategy \
descriptions into structured YAML matching this exact schema.

Output ONLY valid YAML (no markdown fences, no explanation before/after the YAML).

After the YAML, on a new line starting with "EXPLANATION:", provide a brief \
1-2 sentence summary of what you understood.

Required YAML schema:
```
name: <descriptive name>
version: "1.0"
description: <original description>
ticker: <SPX or SPY, default SPX>
structure:
  strategy_type: <iron_condor|vertical_spread|straddle|strangle|naked_put|naked_call|butterfly|calendar|custom>
  legs:
    - name: <leg_name>
      side: <call|put>
      action: <buy|sell>
      delta_target: <fixed|range|atm|otm>
      delta_value: <0.0-1.0>
      quantity: <int, default 1>
  dte_target: <int, default 30>
  dte_min: <int>
  dte_max: <int>
entry:
  iv_rank_min: <0-100>
  iv_rank_max: <0-100>
  vix_min: <float>
  vix_max: <float>
  time_of_day: <open|close|any>
exit:
  profit_target_pct: <0.0-1.0, e.g. 0.50 for 50%>
  stop_loss_pct: <float, e.g. 2.0 for 200% of max profit>
  dte_close: <int, days before expiry to close>
sizing:
  max_risk_pct: <0.0-1.0>
  max_positions: <int>
tags: [<list of tags>]
```

Iron condor example (4 legs): short_put, long_put, short_call, long_call.
Vertical spread example (2 legs): short leg + long leg, same side.
Straddle/strangle: sell (or buy) both put and call.

Delta conventions:
- For selling premium: use 0.15-0.20 for wings (15-20 delta)
- ATM = 0.50 delta
- Protection legs are typically 0.05-0.10 delta

When the user says "X delta wings", that means the SHORT legs are at X delta.
Protection legs should be 5-10 delta further OTM.

If the description is ambiguous or missing critical info, still produce \
your best guess YAML but note what you assumed in the EXPLANATION.\
"""

REFINE_SYSTEM_PROMPT = """\
You are an options strategy editor. Given an existing strategy YAML and \
the user's modification request, output the COMPLETE modified YAML.

Output ONLY valid YAML (no markdown fences), followed by \
"EXPLANATION:" on a new line with a brief summary of what you changed.

Preserve all fields from the original that aren't being modified.\
"""


class StrategyParser:
    """Parses natural language strategy descriptions into StrategyTemplate.

    Uses Claude Sonnet to convert plain English into structured YAML,
    then validates the result against the strategy schema.

    Args:
        api_key: Claude API key. Defaults to config.claude_api_key.
        model: Claude model to use. Defaults to config.claude_model.
    """

    _MAX_RETRIES = 2
    _RETRY_DELAY = 1.0  # seconds

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        self._api_key = api_key or config.claude_api_key
        self._model = model or config.claude_model
        self._loader = StrategyLoader()
        self._client: anthropic.AsyncAnthropic | None = None

    @property
    def client(self) -> anthropic.AsyncAnthropic:
        """Lazy-initialized, reusable AsyncAnthropic client (W9)."""
        if self._client is None:
            self._client = anthropic.AsyncAnthropic(
                api_key=self._api_key,
                timeout=httpx.Timeout(60.0, connect=10.0),  # W3
            )
        return self._client

    async def _call_with_retry(
        self,
        system: str,
        user_content: str,
    ) -> str:
        """Call Claude API with retry for transient errors (W10).

        Args:
            system: System prompt.
            user_content: User message content.

        Returns:
            Response text from Claude.

        Raises:
            StrategyParseError: After all retries exhausted.
        """
        last_exc: Exception | None = None
        for attempt in range(1 + self._MAX_RETRIES):
            try:
                message = await self.client.messages.create(
                    model=self._model,
                    max_tokens=2048,
                    system=system,
                    messages=[
                        {"role": "user", "content": user_content},
                    ],
                )
                response_text = ""
                for block in message.content:
                    if block.type == "text":
                        response_text += block.text
                return response_text.strip()
            except anthropic.RateLimitError as exc:
                last_exc = exc
                if attempt < self._MAX_RETRIES:
                    logger.warning("Rate limited, retrying in %.1fs (attempt %d)", self._RETRY_DELAY, attempt + 1)
                    await asyncio.sleep(self._RETRY_DELAY * (attempt + 1))
            except (anthropic.APIConnectionError, anthropic.InternalServerError) as exc:
                last_exc = exc
                if attempt < self._MAX_RETRIES:
                    logger.warning("Transient API error, retrying: %s", exc)
                    await asyncio.sleep(self._RETRY_DELAY)
            except anthropic.APIError as exc:
                raise StrategyParseError(f"Claude API error: {exc}") from exc

        raise StrategyParseError(f"Claude API error after {self._MAX_RETRIES + 1} attempts: {last_exc}") from last_exc

    async def parse(self, description: str) -> tuple[StrategyTemplate, str]:
        """Parse natural language strategy description into StrategyTemplate.

        Returns (template, explanation) where explanation is Claude's
        interpretation for Borey to confirm.

        Args:
            description: Plain English strategy description.

        Returns:
            Tuple of (StrategyTemplate, explanation string).

        Raises:
            StrategyParseError: If parsing fails (bad API response, invalid YAML, etc.)
        """
        if not self._api_key:
            raise StrategyParseError("Claude API key not configured")

        # W4: Wrap user input in XML delimiters
        user_content = f"<strategy_description>{description}</strategy_description>"
        response_text = await self._call_with_retry(SYSTEM_PROMPT, user_content)
        return self._parse_response(response_text)

    async def refine(
        self,
        template: StrategyTemplate,
        feedback: str,
    ) -> tuple[StrategyTemplate, str]:
        """Refine an existing strategy template based on feedback.

        Args:
            template: Existing strategy template to modify.
            feedback: Natural language modification request.

        Returns:
            Tuple of (modified StrategyTemplate, explanation of changes).

        Raises:
            StrategyParseError: If refinement fails.
        """
        if not self._api_key:
            raise StrategyParseError("Claude API key not configured")

        # Serialize current template to YAML for context
        current_yaml = yaml.dump(
            self._loader._template_to_dict(template),
            default_flow_style=False,
            sort_keys=False,
        )

        # W4: Wrap user input in XML delimiters
        user_content = (
            f"Current strategy YAML:\n```\n{current_yaml}```\n\n"
            f"Modification requested: <user_feedback>{feedback}</user_feedback>"
        )
        response_text = await self._call_with_retry(REFINE_SYSTEM_PROMPT, user_content)
        return self._parse_response(response_text)

    def _parse_response(self, response_text: str) -> tuple[StrategyTemplate, str]:
        """Parse Claude's response into a StrategyTemplate and explanation.

        Expects response format:
            <YAML content>
            EXPLANATION: <text>

        Args:
            response_text: Raw text response from Claude.

        Returns:
            Tuple of (StrategyTemplate, explanation).

        Raises:
            StrategyParseError: If YAML is invalid or template validation fails.
        """
        if not response_text:
            raise StrategyParseError("Empty response from Claude")

        # Split YAML from explanation
        yaml_text = response_text
        explanation = ""

        if "EXPLANATION:" in response_text:
            parts = response_text.split("EXPLANATION:", 1)
            yaml_text = parts[0].strip()
            explanation = parts[1].strip()

        # Strip markdown code fences if present
        yaml_text = self._strip_code_fences(yaml_text)

        # Parse YAML
        try:
            raw = yaml.safe_load(yaml_text)
        except yaml.YAMLError as exc:
            raise StrategyParseError(f"Invalid YAML from Claude: {exc}") from exc

        if not isinstance(raw, dict):
            raise StrategyParseError(
                f"Expected YAML mapping, got {type(raw).__name__}"
            )

        # Convert to StrategyTemplate
        try:
            template = self._loader._dict_to_template(raw)
        except (KeyError, ValueError, TypeError) as exc:
            raise StrategyParseError(
                f"Failed to build StrategyTemplate from Claude output: {exc}"
            ) from exc

        # Validate
        errors = validate_strategy(template)
        if errors:
            raise StrategyParseError(
                "Strategy validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            )

        logger.info(
            "Parsed strategy '%s' (%s, %d legs)",
            template.name,
            template.structure.strategy_type.value,
            len(template.structure.legs),
        )

        return template, explanation

    @staticmethod
    def _strip_code_fences(text: str) -> str:
        """Remove markdown code fences from text."""
        lines = text.split("\n")
        result = []
        in_fence = False

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("```"):
                in_fence = not in_fence
                continue
            result.append(line)

        return "\n".join(result)


class StrategyParseError(Exception):
    """Raised when strategy parsing from natural language fails."""
