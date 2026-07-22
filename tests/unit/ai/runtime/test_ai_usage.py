from decimal import Decimal

import pytest

from sapientia.ai.runtime import (
    AIUsage,
)


def test_total_tokens_are_calculated() -> None:
    usage = AIUsage(
        input_tokens=100,
        output_tokens=40,
    )

    assert usage.total_tokens == 140


def test_explicit_valid_total_tokens() -> None:
    usage = AIUsage(
        input_tokens=100,
        output_tokens=40,
        total_tokens=140,
    )

    assert usage.total_tokens == 140


def test_inconsistent_total_tokens_are_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="total_tokens",
    ):
        AIUsage(
            input_tokens=100,
            output_tokens=40,
            total_tokens=130,
        )


def test_cached_tokens_cannot_exceed_input_tokens() -> None:
    with pytest.raises(
        ValueError,
        match="cached_input_tokens",
    ):
        AIUsage(
            input_tokens=10,
            cached_input_tokens=20,
        )


def test_usage_cost_is_serialised() -> None:
    usage = AIUsage(
        input_tokens=100,
        output_tokens=20,
        estimated_cost=Decimal("0.00125"),
        currency="usd",
    )

    result = usage.to_dict()

    assert result["total_tokens"] == 120
    assert result["estimated_cost"] == "0.00125"
    assert result["currency"] == "USD"