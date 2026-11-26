import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "day01"))

import hello_model  # noqa: E402


def test_system_prompt_asks_for_json():
    assert "JSON" in hello_model.SYSTEM_PROMPT, "the system prompt must ask for JSON output"
