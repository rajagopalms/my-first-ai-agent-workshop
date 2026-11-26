"""Day 2, part 2: download failed GitHub Actions logs and mask them.

For each recent failed run, this runs the same command you would type:
    gh run view <run-id> --log-failed
and saves two copies:
    logs/raw/<run-id>-<branch>.log      the original (git-ignored, never commit it)
    logs/masked/<run-id>-<branch>.log   secrets masked, safe to use in prompts and tests

Usage:
    python day02/fetch_failed_logs.py          # the 5 most recent failed runs
    python day02/fetch_failed_logs.py 10       # the 10 most recent
    python day02/fetch_failed_logs.py --run 45847889567 [more ids]   # specific runs
"""

import json
import re
import subprocess
import sys
from pathlib import Path

from mask_secrets import mask

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "logs" / "raw"
MASKED_DIR = ROOT / "logs" / "masked"


def gh(*args: str) -> str:
    try:
        result = subprocess.run(["gh", *args], capture_output=True, text=True, encoding="utf-8", check=True)
    except FileNotFoundError:
        sys.exit("The GitHub CLI (gh) is not on PATH. Install it and run: gh auth login")
    except subprocess.CalledProcessError as err:
        sys.exit(f"gh {' '.join(args)} failed:\n{err.stderr}")
    return result.stdout


FIELDS = "databaseId,headBranch,displayTitle,workflowName"


def main(limit: int, run_ids: list[str]) -> None:
    if run_ids:
        runs = [json.loads(gh("run", "view", run_id, "--json", FIELDS)) for run_id in run_ids]
    else:
        runs = json.loads(gh("run", "list", "--status", "failure", "--limit", str(limit), "--json", FIELDS))
    if not runs:
        sys.exit("No failed runs found. Push a deliberately broken commit first (see PROGRESS.md, day 2).")

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    MASKED_DIR.mkdir(parents=True, exist_ok=True)

    for run in runs:
        run_id = run["databaseId"]
        branch = re.sub(r"[^A-Za-z0-9._-]+", "-", run["headBranch"]).strip("-")
        name = f"{run_id}-{branch}.log"

        log = gh("run", "view", str(run_id), "--log-failed")
        masked, found = mask(log)

        (RAW_DIR / name).write_text(log, encoding="utf-8")
        (MASKED_DIR / name).write_text(masked, encoding="utf-8")

        lines = log.count("\n")
        print(f"{name:45} {lines:5} lines   masked: {dict(found) or 'nothing'}")

    print(f"\nRaw logs:    {RAW_DIR.relative_to(ROOT)}   (git-ignored)")
    print(f"Masked logs: {MASKED_DIR.relative_to(ROOT)}   (safe to commit)")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["--run"]:
        main(0, args[1:])
    else:
        main(int(args[0]) if args else 5, [])
