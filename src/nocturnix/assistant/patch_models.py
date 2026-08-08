from __future__ import annotations

from dataclasses import dataclass, field


class PatchProposalError(RuntimeError):
    """Raised when a patch proposal cannot be generated safely."""


@dataclass(frozen=True)
class PatchFileChange:
    path: str
    unified_diff: str
    original_sha256: str
    proposed_sha256: str


@dataclass(frozen=True)
class PatchProposalResult:
    """A read-only locally generated code-change proposal."""

    title: str
    summary: str
    affected_files: list[str]
    file_changes: list[PatchFileChange]
    warnings: list[str] = field(default_factory=list)
    generated_locally: bool = True
    applied: bool = False

    @property
    def unified_diff(self) -> str:
        return "\n\n".join(change.unified_diff for change in self.file_changes)

    @property
    def original_sha256(self) -> str:
        if len(self.file_changes) != 1:
            raise ValueError("original_sha256 is only available for single-file patch proposals.")

        return self.file_changes[0].original_sha256

    @property
    def proposed_sha256(self) -> str:
        if len(self.file_changes) != 1:
            raise ValueError("proposed_sha256 is only available for single-file patch proposals.")

        return self.file_changes[0].proposed_sha256
