"""Day 2, part 3: ask the model to explain one failed log in plain words.

The log is trimmed before it is sent: GitHub's per-line timestamps are removed
and only the last lines are kept, because the error is almost always at the end
and every line costs tokens.

Usage:
    python day02/explain_log.py                                  # first file in logs/masked/
    python day02/explain_log.py logs/masked/<file>.log
    python day02/explain_log.py logs/masked/<file>.log --lines 40
"""

import argparse
import re
import sys
from pathlib import Path

from llm import chat

MASKED_DIR = Path(__file__).resolve().parent.parent / "logs" / "masked"

SYSTEM_PROMPT = """You are a senior DevOps engineer helping a teammate read a failed GitHub Actions log.
Explain it in plain words, for someone who did not write the pipeline, using exactly these three headings:

What failed: the step and the command that failed.
Why: the cause, quoting the one or two log lines that prove it.
Fix: one concrete change that would make the run pass.

How to read the log:
- The real error is almost always in the last few lines before "##[error]". Start there and work upwards.
- Lines under "env:" and "with:" are the step's configuration, not errors. An empty value there is a likely cause.
- Do not invent commands, flags or options that do not appear in the log or are not standard for the tool.

Use only what is in the log. If the log does not show the cause, say so instead of guessing.
Reply with only the three headed sections. Do not repeat these instructions."""

# gh --log-failed lines look like: "<job>\t<step>\t2026-11-27T09:12:03.1234567Z <text>"
LINE = re.compile(r"^(?P<job>[^\t]*)\t(?P<step>[^\t]*)\t\S+Z ?(?P<text>.*)$")
# Terminal colour codes, either as real escape characters or as the literal text "^[[36;1m" that gh writes.
ANSI = re.compile(r"(?:\x1b|\^\[)\[[0-9;]*m")


def trim(log: str, max_lines: int) -> str:
    out = []
    for raw in log.splitlines():
        m = LINE.match(raw)
        text = ANSI.sub("", m["text"] if m else raw)
        step = m["step"] if m else ""
        out.append(f"[{step}] {text}" if step else text)
    return "\n".join(out[-max_lines:])


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

    reply = chat(SYSTEM_PROMPT, f"Here is the failed log:\n\n{prompt_log}", temperature=args.temperature)
    print(reply.text)
    print(f"\n--- {reply.usage_line()}")


if __name__ == "__main__":
    main()
