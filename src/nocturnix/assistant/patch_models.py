from __future__ import annotations

from dataclasses import dataclass, field


class PatchProposalError(RuntimeError):
    """Raised when a patch proposal cannot be generated safely."""


@dataclass(frozen=True)
class PatchProposalResult:
    """A read-only locally generated code-change proposal."""

    title: str
    summary: str
    affected_files: list[str]
    unified_diff: str
    warnings: list[str] = field(default_factory=list)
    generated_locally: bool = True
    applied: bool = False
