import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "day03"))
from triage import triage, validate

MASKED = ROOT / "logs" / "masked"

# (log file name part, expected error_type, keywords: any one must be in failing_step)
CASES = [
    ("lint-unused-import", "lint", ["ruff"]),
    ("missing-package-version", "dependency", ["pip"]),
    ("failing-test", "test", ["pytest"]),
    ("wrong-python-version", "config", ["setup-python"]),
    ("wrong-secret-name", "secret", ["hello_model", "smoke"])
]


@pytest.mark.parametrize("name, expected_type, step_words", CASES)
def test_triage(name, expected_type, step_words):
    path = next(MASKED.glob(f"*{name}*.log"))
    result = triage(path)

    assert validate(result) == [], f"invalid JSON shape: {validate(result)}"
    assert result["error_type"] == expected_type, f"Expected error type {expected_type}, but got {result['error_type']}"
    assert any(word in result["failing_step"].lower() for word in step_words), f"failing_step {result['failing_step']!r} has none of {step_words}"