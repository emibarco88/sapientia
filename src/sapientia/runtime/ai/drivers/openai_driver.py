"""
OpenAI AI driver implementation.
"""

from __future__ import annotations

import json
import os
from time import perf_counter
from typing import Any

from openai import OpenAI

from sapientia.runtime.ai.contracts import (
    AIRequest,
    AIResponse,
    AIUsage,
)
from sapientia.runtime.ai.drivers.abstract_ai_driver import (
    AbstractAIDriver,
)
from sapientia.runtime.ai.exceptions import (
    DriverAuthenticationError,
    DriverExecutionError,
)


class OpenAIDriver(AbstractAIDriver):
    """
    Production OpenAI implementation for the Sapientia AI Runtime.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        api_key = (
            self.configuration.get("api_key")
            or os.getenv("OPENAI_API_KEY")
        )

        if not api_key:
            raise DriverAuthenticationError(
                "OPENAI_API_KEY not configured."
            )

        self._default_model = str(
            self.configuration.get("model")
            or os.getenv(
                "OPENAI_MODEL",
                "gpt-4.1-mini",
            )
        ).strip()

        if not self._default_model:
            raise DriverAuthenticationError(
                "An OpenAI model has not been configured."
            )

        self._client = OpenAI(
            api_key=api_key,
        )

    @property
    def driver_name(self) -> str:
        """
        Return the logical runtime driver name.
        """

        return "OPENAI"

    def execute(
        self,
        request: AIRequest,
    ) -> AIResponse:
        """
        Execute an AI request using the OpenAI Responses API.
        """

        self.validate_request(request)

        model = (
            request.model
            or self._default_model
        )

        request_arguments: dict[str, Any] = {
            "model": model,
            "input": request.prompt,
        }

        if request.max_output_tokens is not None:
            request_arguments[
                "max_output_tokens"
            ] = request.max_output_tokens

        if request.temperature is not None:
            request_arguments[
                "temperature"
            ] = request.temperature

        client = self._client

        if request.timeout_seconds is not None:
            client = self._client.with_options(
                timeout=request.timeout_seconds,
            )

        started_at = perf_counter()

        try:
            response = client.responses.create(
                **request_arguments
            )

            latency_ms = int(
                (
                    perf_counter()
                    - started_at
                )
                * 1000
            )

            response_usage = getattr(
                response,
                "usage",
                None,
            )

            input_tokens = int(
                getattr(
                    response_usage,
                    "input_tokens",
                    0,
                )
                or 0
            )

            output_tokens = int(
                getattr(
                    response_usage,
                    "output_tokens",
                    0,
                )
                or 0
            )

            total_tokens = int(
                getattr(
                    response_usage,
                    "total_tokens",
                    0,
                )
                or (
                    input_tokens
                    + output_tokens
                )
            )

            usage = AIUsage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
            )

            content = str(
                getattr(
                    response,
                    "output_text",
                    "",
                )
                or ""
            ).strip()

            if not content:
                raise DriverExecutionError(
                    "OpenAI returned an empty response."
                )

            parsed_content = None
            warnings: list[str] = []

            if request.response_format == "JSON":
                parsed_content = (
                    self._parse_json_content(
                        content
                    )
                )

                if parsed_content is None:
                    warnings.append(
                        "The OpenAI response could not "
                        "be parsed as JSON."
                    )

            response_metadata = {
                "runtime_request_metadata":
                    dict(
                        request.metadata
                    ),

                "response_status":
                    getattr(
                        response,
                        "status",
                        None,
                    ),
            }

            return AIResponse(
                execution_id=(
                    request.execution_id
                ),
                driver=self.driver_name,
                model=model,
                content=content,
                usage=usage,
                finish_reason=getattr(
                    response,
                    "status",
                    None,
                ),
                external_request_id=getattr(
                    response,
                    "id",
                    None,
                ),
                latency_ms=latency_ms,
                parsed_content=parsed_content,
                metadata=response_metadata,
                warnings=warnings,
            )

        except DriverExecutionError:
            raise

        except Exception as exc:
            raise DriverExecutionError(
                f"OpenAI execution failed: {exc}"
            ) from exc

    @staticmethod
    def _parse_json_content(
        content: str,
    ) -> Any | None:
        """
        Parse JSON returned directly or within a Markdown code fence.
        """

        normalized = str(
            content or ""
        ).strip()

        if normalized.startswith("```"):
            lines = normalized.splitlines()

            if lines:
                lines = lines[1:]

            if (
                lines
                and lines[-1].strip() == "```"
            ):
                lines = lines[:-1]

            normalized = "\n".join(
                lines
            ).strip()

        try:
            return json.loads(
                normalized
            )
        except json.JSONDecodeError:
            return None