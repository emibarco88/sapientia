"""
Module: ai_usage.py

Purpose:
Defines provider-independent token usage and cost information for an
AI execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass(slots=True)
class AIUsage:
    """
    Provider-independent AI usage information.

    Token counts and provider-reported cost values can be populated after
    an AI provider completes a request.
    """

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

    cached_input_tokens: int = 0
    reasoning_tokens: int = 0

    estimated_cost: Decimal | None = None
    currency: str = "USD"

    def __post_init__(self) -> None:
        """
        Validate token counts and calculate total tokens when omitted.
        """

        token_fields = {
            "input_tokens":
                self.input_tokens,

            "output_tokens":
                self.output_tokens,

            "total_tokens":
                self.total_tokens,

            "cached_input_tokens":
                self.cached_input_tokens,

            "reasoning_tokens":
                self.reasoning_tokens,
        }

        for field_name, value in token_fields.items():
            if value < 0:
                raise ValueError(
                    f"{field_name} cannot be negative."
                )

        calculated_total = (
            self.input_tokens
            + self.output_tokens
        )

        if self.total_tokens == 0:
            self.total_tokens = calculated_total

        elif (
            calculated_total > 0
            and self.total_tokens
            != calculated_total
        ):
            raise ValueError(
                "total_tokens must equal input_tokens "
                "plus output_tokens."
            )

        if (
            self.cached_input_tokens
            > self.input_tokens
        ):
            raise ValueError(
                "cached_input_tokens cannot exceed "
                "input_tokens."
            )

        if self.estimated_cost is not None:
            self.estimated_cost = Decimal(
                str(self.estimated_cost)
            )

            if self.estimated_cost < 0:
                raise ValueError(
                    "estimated_cost cannot be negative."
                )

        self.currency = str(
            self.currency or "USD"
        ).strip().upper()

        if not self.currency:
            self.currency = "USD"

    def to_dict(self) -> dict[str, Any]:
        """
        Return an API-safe representation.
        """

        return {
            "input_tokens":
                self.input_tokens,

            "output_tokens":
                self.output_tokens,

            "total_tokens":
                self.total_tokens,

            "cached_input_tokens":
                self.cached_input_tokens,

            "reasoning_tokens":
                self.reasoning_tokens,

            "estimated_cost": (
                str(self.estimated_cost)
                if self.estimated_cost is not None
                else None
            ),

            "currency":
                self.currency,
        }