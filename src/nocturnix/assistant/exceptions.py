from __future__ import annotations


class AssistantError(Exception):
    """Base exception for the assistant subsystem."""


class AssistantTaskNotFoundError(AssistantError):
    """Raised when an assistant task cannot be found."""


class AssistantTaskStateError(AssistantError):
    """Raised when an assistant task transition is invalid."""


class AssistantToolNotFoundError(AssistantError):
    """Raised when a requested assistant tool is not registered."""
