from __future__ import annotations

import re
import shutil
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PHOTO_CATEGORIES = {
    "Intake",
    "Damage",
    "Repair",
    "Completed",
}


class PhotoService:
    def __init__(
        self,
        database_path: Path,
        photo_root: Path | None = None,
    ) -> None:
        self.database_path = Path(database_path)

        if photo_root is None:
            self.photo_root = self.database_path.parent / "repair_photos"
        else:
            self.photo_root = Path(photo_root)

        self.photo_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._ensure_schema()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.database_path,
            timeout=30,
        )

        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")

        return connection

    def _ensure_schema(self) -> None:
        with self.connect() as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS repair_photos (
                    photo_id TEXT PRIMARY KEY,
                    repair_id TEXT NOT NULL,
                    category TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    original_filename TEXT NOT NULL,
                    caption TEXT,
                    created_at TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    FOREIGN KEY (repair_id)
                        REFERENCES repair_tickets(ticket_id)
                )
                """)

            connection.execute("""
                CREATE INDEX IF NOT EXISTS
                    idx_repair_photos_repair_id
                ON repair_photos(repair_id)
                """)

            connection.execute("""
                CREATE INDEX IF NOT EXISTS
                    idx_repair_photos_category
                ON repair_photos(category)
                """)

            connection.commit()

    def _require_repair(
        self,
        repair_id: str,
    ) -> None:
        repair_id = str(repair_id).strip()

        if not repair_id:
            raise ValueError("Repair ID is required.")

        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT ticket_id
                FROM repair_tickets
                WHERE ticket_id = ?
                """,
                (repair_id,),
            ).fetchone()

        if row is None:
            raise ValueError(f"Repair not found: {repair_id}")

    def _next_photo_id(
        self,
        connection: sqlite3.Connection,
    ) -> str:
        rows = connection.execute("""
            SELECT photo_id
            FROM repair_photos
            """).fetchall()

        highest = 0

        for row in rows:
            photo_id = str(row["photo_id"] or "")

            match = re.fullmatch(
                r"RPH(\d{6})",
                photo_id,
            )

            if match is None:
                continue

            highest = max(
                highest,
                int(match.group(1)),
            )

        return f"RPH{highest + 1:06d}"

    @staticmethod
    def _safe_extension(
        source_path: Path,
    ) -> str:
        extension = source_path.suffix.lower()

        allowed_extensions = {
            ".jpg",
            ".jpeg",
            ".png",
            ".webp",
            ".heic",
        }

        if extension not in allowed_extensions:
            raise ValueError(
                "Unsupported photo format. " "Use JPG, JPEG, PNG, WEBP, or HEIC."
            )

        return extension

    @staticmethod
    def _normalize_category(
        category: str,
    ) -> str:
        value = str(category).strip()

        if value not in PHOTO_CATEGORIES:
            raise ValueError(f"Invalid photo category: {value}")

        return value

    def add_photo(
        self,
        repair_id: str,
        source_path: Path,
        *,
        category: str = "Intake",
        caption: str = "",
        created_by: str = "Ryan Brown",
    ) -> dict[str, Any]:
        repair_id = str(repair_id).strip()
        self._require_repair(repair_id)

        source_path = Path(source_path)

        if not source_path.exists():
            raise FileNotFoundError(source_path)

        if not source_path.is_file():
            raise ValueError("Photo source must be a file.")

        category = self._normalize_category(category)

        extension = self._safe_extension(source_path)

        created_by = str(created_by).strip()

        if not created_by:
            created_by = "Ryan Brown"

        caption = str(caption).strip()

        repair_directory = self.photo_root / repair_id

        repair_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        with self.connect() as connection:
            photo_id = self._next_photo_id(connection)

            destination = repair_directory / f"{photo_id}{extension}"

            shutil.copy2(
                source_path,
                destination,
            )

            timestamp = datetime.now(UTC).isoformat()

            connection.execute(
                """
                INSERT INTO repair_photos (
                    photo_id,
                    repair_id,
                    category,
                    file_path,
                    original_filename,
                    caption,
                    created_at,
                    created_by
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    photo_id,
                    repair_id,
                    category,
                    str(destination),
                    source_path.name,
                    caption or None,
                    timestamp,
                    created_by,
                ),
            )

            connection.commit()

        photo = self.get_photo(photo_id)

        if photo is None:
            raise RuntimeError("Photo was created but " "could not be reloaded.")

        return photo

    def get_photo(
        self,
        photo_id: str,
    ) -> dict[str, Any] | None:
        photo_id = str(photo_id).strip()

        if not photo_id:
            return None

        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM repair_photos
                WHERE photo_id = ?
                """,
                (photo_id,),
            ).fetchone()

        if row is None:
            return None

        return dict(row)

    def list_repair_photos(
        self,
        repair_id: str,
    ) -> list[dict[str, Any]]:
        self._require_repair(repair_id)

        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM repair_photos
                WHERE repair_id = ?
                ORDER BY
                    created_at DESC,
                    photo_id DESC
                """,
                (repair_id,),
            ).fetchall()

        return [dict(row) for row in rows]

    def update_photo(
        self,
        photo_id: str,
        *,
        category: str | None = None,
        caption: str | None = None,
    ) -> dict[str, Any]:
        current = self.get_photo(photo_id)

        if current is None:
            raise ValueError(f"Photo not found: {photo_id}")

        new_category = (
            self._normalize_category(category)
            if category is not None
            else str(current["category"])
        )

        new_caption = (
            str(caption).strip()
            if caption is not None
            else str(
                current.get(
                    "caption",
                    "",
                )
                or ""
            )
        )

        with self.connect() as connection:
            connection.execute(
                """
                UPDATE repair_photos
                SET
                    category = ?,
                    caption = ?
                WHERE photo_id = ?
                """,
                (
                    new_category,
                    new_caption or None,
                    photo_id,
                ),
            )

            connection.commit()

        updated = self.get_photo(photo_id)

        if updated is None:
            raise RuntimeError("Photo was updated but " "could not be reloaded.")

        return updated

    def remove_photo(
        self,
        photo_id: str,
        *,
        delete_file: bool = False,
    ) -> bool:
        photo = self.get_photo(photo_id)

        if photo is None:
            return False

        file_path = Path(str(photo["file_path"]))

        with self.connect() as connection:
            connection.execute(
                """
                DELETE FROM repair_photos
                WHERE photo_id = ?
                """,
                (photo_id,),
            )

            connection.commit()

        if delete_file:
            file_path.unlink(missing_ok=True)

        return True
