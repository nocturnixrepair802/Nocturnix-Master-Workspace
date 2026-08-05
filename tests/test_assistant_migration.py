from pathlib import Path

from sqlalchemy import inspect

from nocturnix.db import create_database_engine, current_revision, head_revision, run_migrations


def test_assistant_migration_creates_task_and_result_tables_at_head(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'assistant_migration.db'}"

    run_migrations(database_url)

    assert current_revision(database_url) == "4c7d288f5576"
    assert head_revision() == "4c7d288f5576"

    engine = create_database_engine(database_url)
    try:
        inspector = inspect(engine)
        table_names = set(inspector.get_table_names())
        assert "assistant_tasks" in table_names
        assert "assistant_results" in table_names
    finally:
        engine.dispose()
