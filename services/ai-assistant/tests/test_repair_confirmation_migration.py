from pathlib import Path

from sqlalchemy import inspect

from nocturnix.db import create_database_engine, current_revision, head_revision, run_migrations


def test_repair_confirmation_migration_is_current_head(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'migration.db'}"

    run_migrations(database_url)

    assert current_revision(database_url) == "20260808_002"
    assert head_revision() == "20260808_002"

    engine = create_database_engine(database_url)
    try:
        inspector = inspect(engine)
        assert "repair_confirmations" in inspector.get_table_names()
        columns = {column["name"] for column in inspector.get_columns("repair_confirmations")}
        assert columns == {
            "id",
            "owner_user_id",
            "previous_response_id",
            "tool_name",
            "arguments_json",
            "action_key",
            "created_at",
            "expires_at",
            "consumed_at",
        }
        indexes = {index["name"] for index in inspector.get_indexes("repair_confirmations")}
        assert indexes == {
            "ix_repair_confirmations_owner_user_id",
            "ix_repair_confirmations_expires_at",
            "ix_repair_confirmations_consumed_at",
        }
    finally:
        engine.dispose()
