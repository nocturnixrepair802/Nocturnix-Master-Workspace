from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]

MAPPINGS_DIRECTORY = (
    PROJECT_ROOT / "integrations" / "wordpress" / "wpforms" / "mappings"
)


def load_json(
    path: Path,
) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path.name}: {exc}") from exc


def validate_mapping(
    path: Path,
    data: dict[str, Any],
) -> list[str]:
    errors: list[str] = []

    form_id = str(
        data.get(
            "form_id",
            "",
        )
    ).strip()

    form_title = str(
        data.get(
            "form_title",
            "",
        )
    ).strip()

    fields = data.get("fields")

    if not form_id:
        errors.append("Missing form_id.")

    if not form_title:
        errors.append("Missing form_title.")

    if not isinstance(
        fields,
        dict,
    ):
        errors.append("fields must be a JSON object.")

        return errors

    nocturnix_targets: set[str] = set()

    for field_id, config in fields.items():
        if not isinstance(
            config,
            dict,
        ):
            errors.append(f"Field {field_id} must be an object.")

            continue

        target = str(
            config.get(
                "nocturnix_field",
                "",
            )
        ).strip()

        if not target:
            errors.append(f"Field {field_id} is missing nocturnix_field.")

            continue

        if target in nocturnix_targets:
            errors.append(f"Duplicate nocturnix_field '{target}' inside {path.name}.")

        nocturnix_targets.add(target)

    return errors


def main() -> int:
    if not MAPPINGS_DIRECTORY.exists():
        print("ERROR: mappings directory not found:")

        print(MAPPINGS_DIRECTORY)

        return 1

    mapping_files = sorted(MAPPINGS_DIRECTORY.glob("*.json"))

    if not mapping_files:
        print("ERROR: no mapping JSON files found.")

        return 1

    print("WPForms Mapping Validation")

    print("=" * 60)

    seen_form_ids: dict[str, Path] = {}

    total_errors = 0

    for path in mapping_files:
        print(f"\nChecking: {path.name}")

        try:
            data = load_json(path)
        except ValueError as exc:
            print(f"  FAIL: {exc}")

            total_errors += 1

            continue

        errors = validate_mapping(
            path,
            data,
        )

        form_id = str(
            data.get(
                "form_id",
                "",
            )
        ).strip()

        if form_id:
            existing = seen_form_ids.get(form_id)

            if existing is not None:
                errors.append(
                    f"Duplicate form_id {form_id}; also used by {existing.name}."
                )
            else:
                seen_form_ids[form_id] = path

        if errors:
            for error in errors:
                print(f"  FAIL: {error}")

            total_errors += len(errors)
        else:
            print("  PASS")

            print(f"  Form ID: {form_id}")

            print(f"  Title: {data.get('form_title', '')}")

            print(f"  Fields: {len(data.get('fields', {}))}")

    print("\n" + "=" * 60)

    if total_errors:
        print(f"Validation failed with {total_errors} error(s).")

        return 1

    print("All WPForms mapping files passed validation.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
