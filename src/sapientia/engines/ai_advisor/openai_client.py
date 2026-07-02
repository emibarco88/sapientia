"""
Module: openai_client.py

Purpose:
Thin OpenAI client wrapper used by Sapientia AI Advisor.
"""

import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


class SapientiaOpenAIClient:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

        if not self.api_key:
            raise ValueError("Missing OPENAI_API_KEY in .env")

        self.client = OpenAI(api_key=self.api_key)

    def generate_answer(
        self,
        prompt: str,
        max_output_tokens: int = 1200,
    ) -> dict:
        response = self.client.responses.create(
            model=self.model,
            input=prompt,
            max_output_tokens=max_output_tokens,
        )

        return {
            "model": self.model,
            "answer": response.output_text,
            "response_id": response.id,
            "raw_response": response.model_dump(),
        }