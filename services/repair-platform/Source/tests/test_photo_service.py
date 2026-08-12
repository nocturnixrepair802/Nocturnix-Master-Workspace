from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from desktop.services.photo_service import (
    PhotoService,
)


@pytest.fixture
def database_path(
    tmp_path: Path,
) -> Path:
    path = tmp_path / "operations.sqlite3"

    connection = sqlite3.connect(path)

    try:
        connection.execute("""
            CREATE TABLE repair_tickets (
                ticket_id TEXT PRIMARY KEY
            )
            """)

        connection.execute("""
            INSERT INTO repair_tickets (
                ticket_id
            )
            VALUES ('REP000001')
            """)

        connection.commit()
    finally:
        connection.close()

    return path


@pytest.fixture
def service(
    tmp_path: Path,
    database_path: Path,
) -> PhotoService:
    return PhotoService(
        database_path,
        tmp_path / "photos",
    )


def test_add_photo_copies_file_and_persists_metadata(
    service: PhotoService,
    tmp_path: Path,
) -> None:
    source = tmp_path / "device.jpg"
    source.write_bytes(b"test-image")

    photo = service.add_photo(
        "REP000001",
        source,
        category="Intake",
        caption="Front glass",
        created_by="Test User",
    )

    assert photo["photo_id"] == "RPH000001"
    assert photo["repair_id"] == "REP000001"
    assert photo["category"] == "Intake"
    assert photo["caption"] == "Front glass"
    assert photo["created_by"] == "Test User"
    assert photo["original_filename"] == ("device.jpg")

    copied_path = Path(photo["file_path"])

    assert copied_path.exists()
    assert copied_path.read_bytes() == (b"test-image")


def test_multiple_photos_get_unique_ids(
    service: PhotoService,
    tmp_path: Path,
) -> None:
    first = tmp_path / "first.png"
    second = tmp_path / "second.png"

    first.write_bytes(b"one")
    second.write_bytes(b"two")

    photo_one = service.add_photo(
        "REP000001",
        first,
    )

    photo_two = service.add_photo(
        "REP000001",
        second,
    )

    assert photo_one["photo_id"] == ("RPH000001")
    assert photo_two["photo_id"] == ("RPH000002")


def test_list_repair_photos(
    service: PhotoService,
    tmp_path: Path,
) -> None:
    source = tmp_path / "damage.webp"
    source.write_bytes(b"damage")

    service.add_photo(
        "REP000001",
        source,
        category="Damage",
    )

    photos = service.list_repair_photos("REP000001")

    assert len(photos) == 1
    assert photos[0]["category"] == "Damage"


def test_invalid_category_is_rejected(
    service: PhotoService,
    tmp_path: Path,
) -> None:
    source = tmp_path / "device.jpg"
    source.write_bytes(b"image")

    with pytest.raises(
        ValueError,
        match="Invalid photo category",
    ):
        service.add_photo(
            "REP000001",
            source,
            category="Unknown",
        )


def test_unsupported_extension_is_rejected(
    service: PhotoService,
    tmp_path: Path,
) -> None:
    source = tmp_path / "device.txt"
    source.write_text(
        "not an image",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Unsupported photo format",
    ):
        service.add_photo(
            "REP000001",
            source,
        )


def test_update_photo_metadata(
    service: PhotoService,
    tmp_path: Path,
) -> None:
    source = tmp_path / "device.jpg"
    source.write_bytes(b"image")

    photo = service.add_photo(
        "REP000001",
        source,
    )

    updated = service.update_photo(
        photo["photo_id"],
        category="Completed",
        caption="Finished repair",
    )

    assert updated["category"] == "Completed"
    assert updated["caption"] == ("Finished repair")


def test_remove_photo_preserves_file_by_default(
    service: PhotoService,
    tmp_path: Path,
) -> None:
    source = tmp_path / "device.jpg"
    source.write_bytes(b"image")

    photo = service.add_photo(
        "REP000001",
        source,
    )

    copied_path = Path(photo["file_path"])

    assert service.remove_photo(photo["photo_id"])

    assert service.get_photo(photo["photo_id"]) is None

    assert copied_path.exists()


def test_remove_photo_can_delete_file(
    service: PhotoService,
    tmp_path: Path,
) -> None:
    source = tmp_path / "device.jpg"
    source.write_bytes(b"image")

    photo = service.add_photo(
        "REP000001",
        source,
    )

    copied_path = Path(photo["file_path"])

    assert service.remove_photo(
        photo["photo_id"],
        delete_file=True,
    )

    assert not copied_path.exists()

