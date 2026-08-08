from __future__ import annotations

import fnmatch
import os
from pathlib import Path, PurePosixPath, PureWindowsPath

from nocturnix.assistant.repository_models import (
    RepositoryAccessRequest,
    RepositoryContext,
    RepositoryFileItem,
    RepositoryFileReference,
    RepositoryFileResponse,
    RepositoryFilesResponse,
    RepositorySearchMatch,
    RepositorySearchResponse,
    RepositoryStatusResponse,
)

SAFE_TEXT_EXTENSIONS = frozenset(
    {
        ".py",
        ".pyi",
        ".md",
        ".txt",
        ".toml",
        ".yaml",
        ".yml",
        ".json",
        ".html",
        ".css",
        ".js",
        ".ts",
        ".tsx",
        ".jsx",
        ".sql",
    }
)
IGNORED_NAMES = frozenset(
    {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".pyright",
        "htmlcov",
        "node_modules",
        "dist",
        "build",
    }
)
IGNORED_PATTERNS = (
    ".coverage",
    "*.db",
    "*.sqlite",
    "*.sqlite3",
    ".env",
    ".env.*",
    "*.pem",
    "*.key",
    "*.bak",
)
MAX_CONTEXT_BYTES = 64_000


class RepositoryAccessError(ValueError):
    status_code = 400


class RepositoryNotFoundError(RepositoryAccessError):
    status_code = 404


class RepositoryAccessService:
    def __init__(self, root: Path | str, max_file_bytes: int, search_result_limit: int) -> None:
        self.root = Path(root).expanduser().resolve(strict=True)
        if not self.root.is_dir():
            raise RepositoryAccessError("Repository root is not a directory.")
        self.max_file_bytes = max_file_bytes
        self.search_result_limit = search_result_limit

    def status(self) -> RepositoryStatusResponse:
        indexed, ignored = self._scan_counts()
        return RepositoryStatusResponse(
            status="ok",
            root_name=self.root.name,
            indexed_file_count=indexed,
            ignored_path_count=ignored,
            max_file_bytes=self.max_file_bytes,
        )

    def list_files(
        self,
        *,
        prefix: str | None = None,
        extension: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> RepositoryFilesResponse:
        normalized_prefix = self._normalize_prefix(prefix)
        normalized_extension = self._normalize_extension(extension)
        items = [
            item
            for item in self._safe_files()
            if (not normalized_prefix or item.path.startswith(normalized_prefix))
            and (not normalized_extension or item.extension == normalized_extension)
        ]
        return RepositoryFilesResponse(
            items=items[offset : offset + limit],
            total=len(items),
            limit=limit,
            offset=offset,
        )

    def search(
        self,
        *,
        query: str,
        search_content: bool = True,
        extensions: list[str] | None = None,
        limit: int | None = None,
    ) -> RepositorySearchResponse:
        max_results = min(limit or self.search_result_limit, self.search_result_limit)
        wanted_extensions = {self._normalize_extension(ext) for ext in extensions or []}
        needle = query.casefold()
        matches: list[RepositorySearchMatch] = []
        order = 0
        for item in self._safe_files():
            if wanted_extensions and item.extension not in wanted_extensions:
                continue
            if needle in item.path.casefold():
                matches.append(
                    RepositorySearchMatch(
                        path=item.path,
                        match_type="filename",
                        excerpt=item.path,
                        order=order,
                    )
                )
                order += 1
            if search_content and len(matches) < max_results:
                content = self.read_file(item.path).content
                for line_no, line in enumerate(content.splitlines(), start=1):
                    if needle in line.casefold():
                        matches.append(
                            RepositorySearchMatch(
                                path=item.path,
                                match_type="content",
                                line_number=line_no,
                                excerpt=line.strip()[:240],
                                order=order,
                            )
                        )
                        order += 1
                        break
            if len(matches) >= max_results:
                break
        return RepositorySearchResponse(
            query=query,
            items=matches[:max_results],
            limit=max_results,
        )

    def read_file(self, relative_path: str) -> RepositoryFileResponse:
        path = self._resolve_file(relative_path)
        stat = path.stat()
        if stat.st_size > self.max_file_bytes:
            raise RepositoryAccessError("File is larger than the configured repository read limit.")
        raw = path.read_bytes()
        if b"\x00" in raw:
            raise RepositoryAccessError("Binary files are not available through repository access.")
        try:
            content = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise RepositoryAccessError("File is not valid UTF-8 text.") from exc
        rel = path.relative_to(self.root).as_posix()
        return RepositoryFileResponse(
            path=rel,
            extension=path.suffix.lower(),
            size_bytes=stat.st_size,
            content=content,
            truncated=False,
        )

    def load_context(
        self,
        selected_files: list[str],
    ) -> tuple[str | None, list[str]]:
        if not selected_files:
            return None, []

        parts: list[str] = []
        names: list[str] = []
        total = 0

        for selected in selected_files:
            loaded = self.read_file(selected)
            total += loaded.size_bytes

            if total > MAX_CONTEXT_BYTES:
                raise RepositoryAccessError("Selected repository files exceed the context limit.")

            names.append(loaded.path)
            parts.append(f"File: {loaded.path}\n{loaded.content}")

        return "\n\n".join(parts), names

    def _resolve_file(self, raw_path: str) -> Path:
        if "\x00" in raw_path or "\\" in raw_path:
            raise RepositoryAccessError("Repository path is invalid.")

        posix_path = PurePosixPath(raw_path)
        windows_path = PureWindowsPath(raw_path)

        if (
            posix_path.is_absolute()
            or windows_path.is_absolute()
            or windows_path.drive
            or raw_path.startswith(("//", "\\\\"))
        ):
            raise RepositoryAccessError("Repository path must be relative.")

        if ".." in posix_path.parts:
            raise RepositoryAccessError("Repository path is outside repository root.")

        if any(part in {"", "."} for part in posix_path.parts):
            raise RepositoryAccessError("Repository path contains unsafe segments.")

        try:
            candidate = (self.root / Path(*posix_path.parts)).resolve(strict=True)
        except OSError as exc:
            raise RepositoryNotFoundError("Repository file was not found.") from exc

        if not candidate.is_relative_to(self.root):
            raise RepositoryAccessError("Repository path escapes the configured root.")

        if not candidate.is_file():
            raise RepositoryNotFoundError("Repository file was not found.")

        relative_path = candidate.relative_to(self.root).as_posix()

        if (
            self._ignored(relative_path, candidate)
            or candidate.suffix.lower() not in SAFE_TEXT_EXTENSIONS
        ):
            raise RepositoryAccessError("Repository file is not approved for access.")

        return candidate

    def _safe_files(self) -> list[RepositoryFileItem]:
        items: list[RepositoryFileItem] = []
        for dirpath, dirnames, filenames in os.walk(self.root, followlinks=False):
            base = Path(dirpath)
            dirnames[:] = sorted(
                d
                for d in dirnames
                if not self._ignored((base / d).relative_to(self.root).as_posix(), base / d)
            )
            for name in sorted(filenames):
                path = base / name
                try:
                    rel = path.relative_to(self.root).as_posix()
                    resolved = path.resolve(strict=True)
                    if not resolved.is_relative_to(self.root) or self._ignored(rel, path):
                        continue
                    if (
                        path.suffix.lower() not in SAFE_TEXT_EXTENSIONS
                        or path.stat().st_size > self.max_file_bytes
                    ):
                        continue
                    items.append(
                        RepositoryFileItem(
                            path=rel,
                            extension=path.suffix.lower(),
                            size_bytes=path.stat().st_size,
                        )
                    )
                except OSError:
                    continue
        return sorted(items, key=lambda item: item.path)

    def _scan_counts(self) -> tuple[int, int]:
        indexed = 0
        ignored = 0
        for dirpath, dirnames, filenames in os.walk(self.root, followlinks=False):
            base = Path(dirpath)
            kept_dirs = []
            for dirname in sorted(dirnames):
                if self._ignored(
                    (base / dirname).relative_to(self.root).as_posix(),
                    base / dirname,
                ):
                    ignored += 1
                else:
                    kept_dirs.append(dirname)
            dirnames[:] = kept_dirs
            for filename in filenames:
                path = base / filename
                rel = path.relative_to(self.root).as_posix()
                if (
                    self._ignored(rel, path)
                    or path.suffix.lower() not in SAFE_TEXT_EXTENSIONS
                    or path.stat().st_size > self.max_file_bytes
                ):
                    ignored += 1
                else:
                    indexed += 1
        return indexed, ignored

    def _ignored(self, rel: str, path: Path) -> bool:
        parts = PurePosixPath(rel).parts
        return any(part in IGNORED_NAMES for part in parts) or any(
            fnmatch.fnmatchcase(path.name, pattern) for pattern in IGNORED_PATTERNS
        )

    def _normalize_prefix(self, prefix: str | None) -> str | None:
        if not prefix:
            return None
        self._resolve_relative_only(prefix.rstrip("/"))
        return prefix.strip().replace("\\", "/")

    def _normalize_extension(self, extension: str | None) -> str | None:
        if not extension:
            return None
        ext = extension.lower().strip()
        return ext if ext.startswith(".") else f".{ext}"

    def _resolve_relative_only(self, value: str) -> None:
        if (
            "\x00" in value
            or "\\" in value
            or PurePosixPath(value).is_absolute()
            or PureWindowsPath(value).is_absolute()
            or ".." in PurePosixPath(value).parts
        ):
            raise RepositoryAccessError("Repository path is invalid.")


def _resolve_repository_context_path(
    repository_root: Path,
    raw_path: str,
) -> Path:
    if "\x00" in raw_path or "\\" in raw_path:
        raise RepositoryAccessError("Repository path is invalid.")

    posix_path = PurePosixPath(raw_path)
    windows_path = PureWindowsPath(raw_path)

    if (
        posix_path.is_absolute()
        or windows_path.is_absolute()
        or bool(windows_path.drive)
        or raw_path.startswith(("//", "\\\\"))
    ):
        raise RepositoryAccessError("Repository path must be relative.")

    if ".." in posix_path.parts:
        raise RepositoryAccessError("Repository path is outside repository root.")

    if any(part in {"", "."} for part in posix_path.parts):
        raise RepositoryAccessError("Repository path contains unsafe segments.")

    try:
        resolved_path = (repository_root / Path(*posix_path.parts)).resolve(strict=True)
    except OSError as exc:
        raise RepositoryNotFoundError("Repository file was not found.") from exc

    if not resolved_path.is_relative_to(repository_root):
        raise RepositoryAccessError("Repository path is outside repository root.")

    if not resolved_path.is_file():
        raise RepositoryNotFoundError("Repository file was not found.")

    relative_path = resolved_path.relative_to(repository_root).as_posix()

    if (
        any(part in IGNORED_NAMES for part in PurePosixPath(relative_path).parts)
        or any(
            fnmatch.fnmatchcase(
                resolved_path.name,
                pattern,
            )
            for pattern in IGNORED_PATTERNS
        )
        or resolved_path.suffix.lower() not in SAFE_TEXT_EXTENSIONS
    ):
        raise RepositoryAccessError("Repository file is not approved for access.")

    return resolved_path


def load_repository_context(
    request: RepositoryAccessRequest,
) -> RepositoryContext:
    try:
        repository_root = Path(request.repository_root).expanduser().resolve(strict=True)
    except OSError as exc:
        raise RepositoryAccessError("Repository root does not exist.") from exc

    if not repository_root.is_dir():
        raise RepositoryAccessError("Repository root is not a directory.")

    if len(request.selected_files) > request.max_file_count:
        raise RepositoryAccessError("Selected repository file count exceeds the configured limit.")

    files: list[RepositoryFileReference] = []

    for selected_path in request.selected_files:
        resolved_path = _resolve_repository_context_path(
            repository_root,
            selected_path,
        )

        raw_content = resolved_path.read_bytes()

        if len(raw_content) > request.max_file_content_length:
            raw_content = raw_content[: request.max_file_content_length]

        if b"\x00" in raw_content:
            raise RepositoryAccessError("Binary files are not available through repository access.")

        try:
            content = raw_content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise RepositoryAccessError("File is not valid UTF-8 text.") from exc

        relative_path = resolved_path.relative_to(repository_root).as_posix()

        files.append(
            RepositoryFileReference(
                path=relative_path,
                content=content,
            )
        )

    return RepositoryContext(
        repository_root=str(repository_root),
        files=files,
    )


def build_repository_context_text(
    context: RepositoryContext,
) -> str:
    if not context.files:
        return ""

    return "\n\n".join(f"File: {file.path}\n{file.content}" for file in context.files)
