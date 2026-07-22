"""
Module: exceptions.py

Purpose:
Defines Enterprise AI Engine exceptions.
"""


class EnterpriseAIError(RuntimeError):
    """
    Base exception for Enterprise AI failures.
    """


class AIProviderConfigurationError(EnterpriseAIError):
    """
    Raised when an AI provider is incorrectly configured.
    """


class AIProviderExecutionError(EnterpriseAIError):
    """
    Raised when an AI provider fails during execution.
    """


class AIProviderNotRegisteredError(EnterpriseAIError):
    """
    Raised when a requested provider has not been registered.
    """


class AIProviderLoadError(EnterpriseAIError):
    """
    Raised when a registered provider cannot be loaded.
    """


class UnsupportedAICapabilityError(EnterpriseAIError):
    """
    Raised when an unsupported AI capability is requested.
    """