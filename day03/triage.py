"""Day 3: triage one failed log and get the answer back as JSON.

Same flow as day02/explain_log.py, but the system prompt lives in
prompts/triage_system.md and the reply is parsed as JSON instead of printed as text.

Usage:
    python day03/triage.py                                  # first file in logs/masked/
    python day03/triage.py logs/masked/<file>.log
    python day03/triage.py logs/masked/<file>.log --lines 40
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MASKED_DIR = ROOT / "logs" / "masked"
PROMPT_FILE = ROOT / "prompts" / "triage_system.md"

# Reuse the day 2 code instead of copying it: put day02/ on the import path.
sys.path.insert(0, str(ROOT / "day02"))
from explain_log import trim
from llm import chat

SYSTEM_PROMPT = PROMPT_FILE.read_text(encoding="utf-8")

# The JSON shape the prompt asks for. Keep these in sync with prompts/triage_system.md.
REQUIRED_KEYS = {"failing_step", "error_type", "likely_cause", "evidence", "fix", "confidence"}
ERROR_TYPES = {"lint", "dependency", "test", "config", "secret", "unknown"}
CONFIDENCE = {"low", "medium", "high"}


def validate(data) -> list[str]:
    """Return a list of problems. An empty list means the reply is valid."""
    if not isinstance(data, dict):
        return [f"expected a JSON object, got {type(data).__name__}"]
    problems = []
    for key in REQUIRED_KEYS:
        if key not in data:
            problems.append(f"missing key: {key}")
    for key in set(data) - REQUIRED_KEYS:
        problems.append(f"unexpected key: {key}")
    if data.get("error_type") not in ERROR_TYPES:
        problems.append(f"bad error_type: {data.get('error_type')!r}")
    if data.get("confidence") not in CONFIDENCE:
        problems.append(f"bad confidence: {data.get('confidence')!r}")
    return problems


def triage(path: Path, lines: int = 80, temperature: float = 0.0) -> dict:
    """Triage one masked log file and return the parsed JSON reply."""
    if "raw" in path.parts:
        raise ValueError("That is a raw log. Use the masked copy in logs/masked/ so no secrets reach the model.")
    log = path.read_text(encoding="utf-8-sig")
    prompt_log = trim(log, lines)
    reply = chat(SYSTEM_PROMPT, f"Here is the failed log:\n\n{prompt_log}",
                 temperature=temperature, max_tokens=500, json_mode=True)
    return json.loads(reply.text)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("log", nargs="?", help="a masked log file (default: first in logs/masked/)")
    parser.add_argument("--lines", type=int, default=80, help="keep only the last N lines (default 80)")
    # 0 = most repeatable. For diagnosis we want the same answer every time, not creativity.
    parser.add_argument("--temperature", type=float, default=0.0)
    args = parser.parse_args()

    if args.log:
        path = Path(args.log)
    else:
        files = sorted(MASKED_DIR.glob("*.log"))
        if not files:
            sys.exit("No masked logs yet. Run: python day02/fetch_failed_logs.py")
        path = files[0]

    if "raw" in path.parts:
        sys.exit("That is a raw log. Use the masked copy in logs/masked/ so no secrets reach the model.")

    log = path.read_text(encoding="utf-8-sig")  # -sig drops the byte-order mark gh adds
    prompt_log = trim(log, args.lines)
    print(f"Log: {path.name}  ({len(log):,} chars -> {len(prompt_log):,} chars after trimming)\n")

    # 500 tokens so the JSON is not cut off halfway (finish: length = broken JSON).
    reply = chat(SYSTEM_PROMPT, f"Here is the failed log:\n\n{prompt_log}",
                 temperature=args.temperature, max_tokens=500, json_mode=True)

    try:
        data = json.loads(reply.text)
    except json.JSONDecodeError as err:
        print(f"NOT VALID JSON ({err}). Raw reply:\n")
        print(reply.text)
    else:
        print(json.dumps(data, indent=2))
        problems = validate(data)
        if problems:
            print("\nINVALID:")
            for p in problems:
                print(f"  - {p}")
        else:
            print("\nVALID")

    print(f"\n--- {reply.usage_line()}")


if __name__ == "__main__":
    main()
