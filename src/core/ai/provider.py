from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class AiProvider(ABC):
    @abstractmethod
    def complete(self, prompt: str, *, system: str | None = None) -> str:
        """Return plain text completion."""
        raise NotImplementedError

    @abstractmethod
    def classify_intent(self, command: str, skill_index: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Return structured intent result.

        Expected output:
        {
            "status": "matched" | "capability_not_available" | "error",
            "intent": "...",
            "skill_name": "...",
            "confidence": 0.0,
            "parameters": {},
            "message": "..."
        }
        """
        raise NotImplementedError

    @abstractmethod
    def summarize_result(self, command: str, result: dict[str, Any]) -> str:
        """Summarize skill execution result for user."""
        raise NotImplementedError

