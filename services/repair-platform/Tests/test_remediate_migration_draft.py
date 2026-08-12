import pytest

pytest.skip(
    "Legacy migration remediation tests depend on implementation "
    "modules that are not tracked in the current repair-platform repository.",
    allow_module_level=True,
)
