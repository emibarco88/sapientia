"""
Module: openai_provider.py

Purpose:
OpenAI provider adapter for Sapientia's Enterprise AI Engine.
"""

from __future__ import annotations

import os
import time
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from sapientia.engines.enterprise_ai.exceptions import (
    AIProviderConfigurationError,
    AIProviderExecutionError,
)
from sapientia.engines.enterprise_ai.models import (
    AIRequest,
    AIResponse,
)
from sapientia.engines.enterprise_ai.providers.base import (
    AIProvider,
)


load_dotenv()


class OpenAIProvider(AIProvider):
    """
    Executes Enterprise AI requests using the OpenAI Responses API.
    """

    def __init__(
        self,
        api_key: str | None = None,
        default_model: str | None = None,
    ) -> None:
        self.api_key = (
            api_key
            or os.getenv("OPENAI_API_KEY")
        )

        self.default_model = (
            default_model
            or os.getenv(
                "OPENAI_MODEL",
                "gpt-4.1-mini",
            )
        )

        if not self.api_key:
            raise AIProviderConfigurationError(
                "Missing OPENAI_API_KEY in .env"
            )

        self.client = OpenAI(
            api_key=self.api_key
        )

    @property
    def provider_name(self) -> str:
        return "OPENAI"

    def generate(
        self,
        request: AIRequest,
    ) -> AIResponse:
        model = (
            request.model
            or self.default_model
        )

        started_at = time.perf_counter()

        try:
            response = (
                self.client.responses.create(
                    model=model,
                    input=request.prompt,
                    max_output_tokens=(
                        request.max_output_tokens
                    ),
                )
            )

        except Exception as exc:
            execution_time_ms = int(
                (
                    time.perf_counter()
                    - started_at
                )
                * 1000
            )

            raise AIProviderExecutionError(
                "OpenAI generation failed "
                f"after {execution_time_ms} ms: "
                f"{exc}"
            ) from exc

        execution_time_ms = int(
            (
                time.perf_counter()
                - started_at
            )
            * 1000
        )

        raw_response = response.model_dump()

        usage = self._extract_usage(
            raw_response
        )

        content = str(
            response.output_text or ""
        ).strip()

        warnings: list[str] = []

        if not content:
            warnings.append(
                "The provider returned no output text."
            )

        return AIResponse(
            success=bool(content),
            capability=request.capability,
            provider=self.provider_name,
            model=model,
            content=content,
            response_id=getattr(
                response,
                "id",
                None,
            ),
            input_tokens=usage.get(
                "input_tokens"
            ),
            output_tokens=usage.get(
                "output_tokens"
            ),
            total_tokens=usage.get(
                "total_tokens"
            ),
            execution_time_ms=(
                execution_time_ms
            ),
            metadata={
                **request.metadata,
                "provider_status": getattr(
                    response,
                    "status",
                    None,
                ),
            },
            warnings=warnings,
            raw_response=raw_response,
        )

    @staticmethod
    def _extract_usage(
        raw_response: dict[str, Any],
    ) -> dict[str, int | None]:
        """
        Extract token usage without tightly coupling Sapientia to
        a specific SDK response class.
        """

        usage = (
            raw_response.get("usage")
            or {}
        )

        input_tokens = usage.get(
            "input_tokens"
        )

        output_tokens = usage.get(
            "output_tokens"
        )

        total_tokens = usage.get(
            "total_tokens"
        )

        if (
            total_tokens is None
            and input_tokens is not None
            and output_tokens is not None
        ):
            total_tokens = (
                input_tokens
                + output_tokens
            )

        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
        }