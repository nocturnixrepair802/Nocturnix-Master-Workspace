from __future__ import annotations


class MockCodingProvider:
    """Deterministic local coding provider for development and UI tests."""

    provider = "mock"
    model = "nocturnix-mock"

    def answer(self, message: str, context: str | None = None) -> str:
        context_note = ""
        if context:
            attached = [
                line[4:-4].strip()
                for line in context.splitlines()
                if line.startswith("--- ") and line.endswith(" ---")
            ]
            if attached:
                context_note = (
                    "\n\nRepository files attached "
                    "(mock mode names them without semantic analysis):\n"
                    + "\n".join(f"- {name}" for name in attached)
                )
            else:
                context_note = (
                    "\n\nProject context was supplied as untrusted local reference text, "
                    "but mock mode does not analyze repository files."
                )
        return (
            "Mock development response\n\n"
            f"Your request was:\n{message}\n\n"
            "The local mock provider is active. Task creation, persistence, "
            "authentication, API routing, and browser rendering are operating "
            "without an external model request. Responses are deterministic and "
            "do not consume API credits."
            f"{context_note}"
        )


__all__ = ["MockCodingProvider"]
