"""
Module: exceptions.py

Purpose:
Defines Enterprise AI Engine exceptions.
"""


class EnterpriseAIError(RuntimeError):
    """
    Base exception for Enterprise AI failures.
    """


class AIProviderConfigurationError(
    EnterpriseAIError
):
    """
    Raised when an AI provider is incorrectly configured.
    """


class AIProviderExecutionError(
    EnterpriseAIError
):
    """
    Raised when an AI provider fails during execution.
    """


class UnsupportedAICapabilityError(
    EnterpriseAIError
):
    """
    Raised when an unsupported AI capability is requested.
    """