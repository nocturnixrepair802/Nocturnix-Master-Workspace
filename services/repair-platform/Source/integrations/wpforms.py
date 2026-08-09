from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class WPFormsMappingError(RuntimeError):
    pass


class WPFormsMapper:
    def __init__(
        self,
        mappings_directory: str | Path,
    ) -> None:
        self.mappings_directory = Path(mappings_directory)

        if not self.mappings_directory.exists():
            raise WPFormsMappingError(
                f"WPForms mappings directory does not exist: {self.mappings_directory}"
            )

    def load_mapping(
        self,
        form_id: str,
    ) -> dict[str, Any]:
        form_id = str(form_id).strip()

        if not form_id:
            raise WPFormsMappingError("WPForms form_id is required.")

        for path in self.mappings_directory.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (
                json.JSONDecodeError,
                OSError,
            ) as exc:
                raise WPFormsMappingError(f"Unable to read mapping: {path}") from exc

            if (
                str(
                    data.get(
                        "form_id",
                        "",
                    )
                )
                == form_id
            ):
                return data

        raise WPFormsMappingError(f"No WPForms mapping found for form_id {form_id}.")

    def map_submission(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        form_id = self._extract_form_id(payload)

        mapping = self.load_mapping(form_id)

        submitted_fields = self._extract_fields(payload)

        mapped: dict[str, Any] = {}

        field_mappings = mapping.get(
            "fields",
            {},
        )

        if not isinstance(
            field_mappings,
            dict,
        ):
            raise WPFormsMappingError("Mapping fields must be an object.")

        for field_id, config in field_mappings.items():
            if not isinstance(
                config,
                dict,
            ):
                continue

            nocturnix_field = str(
                config.get(
                    "nocturnix_field",
                    "",
                )
            ).strip()

            if not nocturnix_field:
                continue

            value = self._get_field_value(
                submitted_fields,
                str(field_id),
            )

            if value is None:
                continue

            mapped[nocturnix_field] = value

        return {
            "form_id": form_id,
            "form_title": str(
                mapping.get(
                    "form_title",
                    "",
                )
            ),
            "mapping_version": mapping.get(
                "version",
                1,
            ),
            "fields": mapped,
            "raw": payload,
        }

    @staticmethod
    def _extract_form_id(
        payload: dict[str, Any],
    ) -> str:
        possible_values = [
            payload.get("form_id"),
            payload.get("id"),
        ]

        form_data = payload.get("form_data")

        if isinstance(
            form_data,
            dict,
        ):
            possible_values.extend(
                [
                    form_data.get("id"),
                    form_data.get("form_id"),
                ]
            )

        entry = payload.get("entry")

        if isinstance(
            entry,
            dict,
        ):
            possible_values.extend(
                [
                    entry.get("form_id"),
                    entry.get("form"),
                ]
            )

        for value in possible_values:
            if value is not None and str(value).strip():
                return str(value).strip()

        raise WPFormsMappingError("Unable to determine WPForms form_id.")

    @staticmethod
    def _extract_fields(
        payload: dict[str, Any],
    ) -> Any:
        possible_fields = [
            payload.get("fields"),
            payload.get("fields_json"),
        ]

        entry = payload.get("entry")

        if isinstance(
            entry,
            dict,
        ):
            possible_fields.extend(
                [
                    entry.get("fields"),
                    entry.get("fields_json"),
                ]
            )

        for value in possible_fields:
            if value is None:
                continue

            if isinstance(
                value,
                str,
            ):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    continue

            return value

        raise WPFormsMappingError("Unable to locate WPForms fields.")

    @staticmethod
    def _get_field_value(
        fields: Any,
        field_id: str,
    ) -> Any:
        if isinstance(
            fields,
            dict,
        ):
            field = fields.get(field_id)

            if field is None:
                field = fields.get(int(field_id) if field_id.isdigit() else field_id)

            return WPFormsMapper._normalize_field_value(field)

        if isinstance(
            fields,
            list,
        ):
            for field in fields:
                if not isinstance(
                    field,
                    dict,
                ):
                    continue

                current_id = str(
                    field.get(
                        "id",
                        "",
                    )
                )

                if current_id == field_id:
                    return WPFormsMapper._normalize_field_value(field)

        return None

    @staticmethod
    def _normalize_field_value(
        field: Any,
    ) -> Any:
        if field is None:
            return None

        if not isinstance(
            field,
            dict,
        ):
            return field

        for key in (
            "value",
            "value_raw",
            "value_choice",
            "value_choice_name",
        ):
            if key in field and field[key] is not None:
                return field[key]

        first = field.get("first")

        last = field.get("last")

        if first is not None or last is not None:
            return {
                "first_name": str(first or ""),
                "last_name": str(last or ""),
            }

        return field
