import pytest

pytest.skip(
    "Legacy migration audit tests depend on an implementation "
    "that is not tracked in the current repair-platform repository.",
    allow_module_level=True,
)
