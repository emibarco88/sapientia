"""
OpenAI AI driver implementation.
"""

from __future__ import annotations

import os

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
    DriverRateLimitError,
    DriverTimeoutError,
)


class OpenAIDriver(AbstractAIDriver):
    """
    Production OpenAI implementation.
    """

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        api_key = (
            self.configuration.get("api_key")
            or os.getenv("OPENAI_API_KEY")
        )

        if not api_key:
            raise DriverAuthenticationError(
                "OPENAI_API_KEY not configured."
            )

        self._client = OpenAI(
            api_key=api_key,
        )

    @property
    def driver_name(self) -> str:
        return "OPENAI"

    def execute(
        self,
        request: AIRequest,
    ) -> AIResponse:

        self.validate_request(request)

        try:

            response = self._client.responses.create(
                model=request.model,
                input=request.prompt,
            )

            usage = AIUsage(
                prompt_tokens=response.usage.input_tokens,
                completion_tokens=response.usage.output_tokens,
                total_tokens=response.usage.total_tokens,
            )

            return AIResponse(
                success=True,
                driver=self.driver_name,
                model=request.model,
                content=response.output_text,
                usage=usage,
                metadata={},
            )

        except Exception as ex:
            raise DriverExecutionError(str(ex)) from ex