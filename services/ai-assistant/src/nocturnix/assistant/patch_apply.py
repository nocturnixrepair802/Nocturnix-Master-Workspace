from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from tempfile import NamedTemporaryFile

from nocturnix.assistant.patch_models import PatchProposalError
from nocturnix.assistant.repository_access import RepositoryAccessError
from nocturnix.assistant.service import AssistantTaskService
from nocturnix.persistence.models import (
    AssistantPatchProposalFileRow,
    AssistantPatchProposalRow,
)


class PatchApplyError(RuntimeError):
    """Raised when a persisted patch proposal cannot be applied safely."""


@dataclass(frozen=True)
class PreparedPatchFile:
    path: Path
    original_content: str
    proposed_content: str
    proposed_sha256: str


class PatchApplyService:
    def __init__(
        self,
        task_service: AssistantTaskService,
    ) -> None:
        self._task_service = task_service

    def apply(
        self,
        proposal_id: str,
        *,
        owner_user_id: str,
        applied_by_user_id: str,
    ) -> AssistantPatchProposalRow:
        proposal = self._task_service.get_patch_proposal(
            proposal_id,
            owner_user_id=owner_user_id,
        )

        if proposal.status != "pending":
            raise PatchApplyError(
                f"Patch proposal {proposal.id!r} cannot be applied "
                f"while its status is {proposal.status!r}."
            )

        try:
            file_changes = self._task_service.list_patch_proposal_files(
                proposal.id,
                owner_user_id=owner_user_id,
            )

            if not file_changes:
                file_changes = [self._legacy_file_change(proposal)]

            prepared_files = [
                self._prepare_file_change(
                    proposal,
                    change,
                )
                for change in file_changes
            ]

            self._apply_prepared_files(prepared_files)

        except (
            OSError,
            UnicodeDecodeError,
            RepositoryAccessError,
            PatchProposalError,
            PatchApplyError,
        ) as exc:
            self._mark_failed(
                proposal,
                owner_user_id=owner_user_id,
                reason=str(exc),
            )

            if isinstance(
                exc,
                PatchApplyError,
            ):
                raise

            raise PatchApplyError(str(exc)) from exc

        return self._task_service.mark_patch_proposal_applied(
            proposal.id,
            owner_user_id=owner_user_id,
            applied_by_user_id=applied_by_user_id,
        )

    def _prepare_file_change(
        self,
        proposal: AssistantPatchProposalRow,
        change: AssistantPatchProposalFileRow,
    ) -> PreparedPatchFile:
        target_path = self._resolve_target_path(
            proposal.repository_root,
            change.path,
        )

        original_bytes = target_path.read_bytes()

        original_content = original_bytes.decode("utf-8")

        current_sha256 = sha256(original_bytes).hexdigest()

        if current_sha256 != change.original_sha256:
            raise PatchApplyError("The target file changed after the patch proposal was generated.")

        proposed_content = self._apply_unified_diff(
            original_content,
            change.unified_diff,
        )

        reconstructed_sha256 = sha256(proposed_content.encode("utf-8")).hexdigest()

        if reconstructed_sha256 != change.proposed_sha256:
            raise PatchApplyError(
                "The reconstructed patched file does not match the stored proposal hash."
            )

        return PreparedPatchFile(
            path=target_path,
            original_content=original_content,
            proposed_content=proposed_content,
            proposed_sha256=(change.proposed_sha256),
        )

    def _apply_prepared_files(
        self,
        prepared_files: list[PreparedPatchFile],
    ) -> None:
        written_files: list[PreparedPatchFile] = []

        try:
            for prepared in prepared_files:
                self._atomic_write(
                    prepared.path,
                    prepared.proposed_content,
                )

                written_files.append(prepared)

                written_sha256 = sha256(prepared.path.read_bytes()).hexdigest()

                if written_sha256 != prepared.proposed_sha256:
                    raise PatchApplyError("Patch verification failed after writing the file.")

        except (
            OSError,
            PatchApplyError,
        ) as exc:
            rollback_error = self._rollback_files(written_files)

            if rollback_error is not None:
                raise PatchApplyError(
                    f"Patch application failed and rollback was incomplete: {rollback_error}"
                ) from exc

            if isinstance(
                exc,
                PatchApplyError,
            ):
                raise

            raise PatchApplyError(str(exc)) from exc

    def _rollback_files(
        self,
        written_files: list[PreparedPatchFile],
    ) -> str | None:
        errors: list[str] = []

        for prepared in reversed(written_files):
            try:
                self._atomic_write(
                    prepared.path,
                    prepared.original_content,
                )
            except OSError as exc:
                errors.append(f"{prepared.path}: {exc}")

        if errors:
            return "; ".join(errors)

        return None

    @staticmethod
    def _legacy_file_change(
        proposal: AssistantPatchProposalRow,
    ) -> AssistantPatchProposalFileRow:
        return AssistantPatchProposalFileRow(
            id="legacy",
            proposal_id=proposal.id,
            ordinal=0,
            path=proposal.target_file,
            unified_diff=proposal.unified_diff,
            original_sha256=proposal.original_sha256,
            proposed_sha256=proposal.proposed_sha256,
            created_at=proposal.created_at,
        )

    @staticmethod
    def _resolve_target_path(
        repository_root_value: str,
        relative_path_value: str,
    ) -> Path:
        repository_root = Path(repository_root_value).expanduser().resolve(strict=True)

        if not repository_root.is_dir():
            raise PatchApplyError("The stored repository root is not a directory.")

        relative_path = Path(relative_path_value)

        if relative_path.is_absolute():
            raise PatchApplyError("Absolute patch target paths are not allowed.")

        if ".." in relative_path.parts:
            raise PatchApplyError("Patch target path traversal is not allowed.")

        target_path = (repository_root / relative_path).resolve(strict=True)

        if target_path != repository_root and repository_root not in target_path.parents:
            raise PatchApplyError("The patch target is outside the repository root.")

        if not target_path.is_file():
            raise PatchApplyError("The patch target is not a file.")

        return target_path

    @staticmethod
    def _resolve_target(
        proposal: AssistantPatchProposalRow,
    ) -> Path:
        return PatchApplyService._resolve_target_path(
            proposal.repository_root,
            proposal.target_file,
        )

    @staticmethod
    def _apply_unified_diff(
        original_content: str,
        unified_diff: str,
    ) -> str:
        original_lines = original_content.splitlines(keepends=True)

        diff_lines = unified_diff.splitlines()

        if len(diff_lines) < 3:
            raise PatchApplyError("The stored unified diff is incomplete.")

        line_index = 0

        if diff_lines[line_index].startswith("--- "):
            line_index += 1

        if line_index < len(diff_lines) and diff_lines[line_index].startswith("+++ "):
            line_index += 1

        result: list[str] = []
        original_index = 0
        saw_hunk = False

        while line_index < len(diff_lines):
            line = diff_lines[line_index]

            if not line:
                line_index += 1
                continue

            if not line.startswith("@@ "):
                line_index += 1
                continue

            saw_hunk = True

            old_start = PatchApplyService._parse_old_start(line)

            target_index = max(
                0,
                old_start - 1,
            )

            if target_index < original_index:
                raise PatchApplyError("The stored unified diff contains overlapping hunks.")

            result.extend(original_lines[original_index:target_index])

            original_index = target_index

            line_index += 1

            while line_index < len(diff_lines):
                diff_line = diff_lines[line_index]

                if diff_line.startswith("@@ "):
                    break

                if not diff_line:
                    line_index += 1
                    continue

                if diff_line == "\\ No newline at end of file":
                    line_index += 1
                    continue

                marker = diff_line[0]
                text = diff_line[1:]

                if marker == " ":
                    expected = PatchApplyService._line_text(
                        original_lines,
                        original_index,
                    )

                    if expected != text:
                        raise PatchApplyError("The patch context does not match the current file.")

                    result.append(original_lines[original_index])

                    original_index += 1

                elif marker == "-":
                    expected = PatchApplyService._line_text(
                        original_lines,
                        original_index,
                    )

                    if expected != text:
                        raise PatchApplyError("The patch removal does not match the current file.")

                    original_index += 1

                elif marker == "+":
                    newline = "\r\n" if "\r\n" in original_content else "\n"

                    result.append(text + newline)

                else:
                    raise PatchApplyError(
                        "The stored unified diff contains an unsupported line type."
                    )

                line_index += 1

        if not saw_hunk:
            raise PatchApplyError("The stored unified diff contains no patch hunks.")

        result.extend(original_lines[original_index:])

        return "".join(result)

    @staticmethod
    def _parse_old_start(
        hunk_header: str,
    ) -> int:
        try:
            old_range = hunk_header.split()[1]

            old_start = old_range[1:].split(",")[0]

            return int(old_start)

        except (
            IndexError,
            ValueError,
        ) as exc:
            raise PatchApplyError(
                "The stored unified diff contains an invalid hunk header."
            ) from exc

    @staticmethod
    def _line_text(
        lines: list[str],
        index: int,
    ) -> str:
        if index >= len(lines):
            raise PatchApplyError(
                "The patch references content beyond the end of the current file."
            )

        return lines[index].rstrip("\r\n")

    @staticmethod
    def _atomic_write(
        target_path: Path,
        content: str,
    ) -> None:
        parent = target_path.parent

        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            dir=parent,
            prefix=(f".{target_path.name}."),
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)

            handle.write(content)
            handle.flush()

        try:
            temporary_path.replace(target_path)
        except OSError:
            temporary_path.unlink(missing_ok=True)
            raise

    def _mark_failed(
        self,
        proposal: AssistantPatchProposalRow,
        *,
        owner_user_id: str,
        reason: str,
    ) -> None:
        try:
            (
                self._task_service.mark_patch_proposal_failed(
                    proposal.id,
                    owner_user_id=owner_user_id,
                    failure_reason=reason[:2000],
                )
            )
        except ValueError:
            pass
