"""Day 2, part 2: mask secrets in logs before they go anywhere near a model.

GitHub already replaces registered repo secrets with *** in Actions logs.
This catches what GitHub does not know about: tokens printed by a tool,
connection strings in error messages, keys pasted into a script, emails.

Use it as a function (mask(text) -> (masked_text, counts)) or from the command line:
    python day02/mask_secrets.py --demo                 # before/after on fake samples
    python day02/mask_secrets.py logs/raw/x.log         # print the masked file
"""

import re
import sys
from collections import Counter

# Each pattern either replaces the whole match, or, if it has a named group
# "keep", keeps that part (the variable name) and masks only the value.
PATTERNS = [
    ("private-key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.DOTALL)),
    ("github-token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{20,})")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}")),
    ("aws-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("bearer", re.compile(r"(?i)(?P<keep>\bbearer[ \t]+)[A-Za-z0-9._~+/-]{12,}=*")),
    (
        "connection-string",
        re.compile(r"(?i)(?P<keep>\b(?:AccountKey|SharedAccessKey|SharedAccessSignature|sig|Password|Pwd)=)[^;&\s\"']+"),
    ),
    (
        "key-value",
        re.compile(
            r"(?i)(?P<keep>\b[A-Z0-9_]*(?:TOKEN|SECRET|API_?KEY|PASSWORD|PASSWD)\b[ \t]*[:=][ \t]*[\"']?)"
            r"(?!\*\*\*)[^\s\"']{8,}"
        ),
    ),
    ("email", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
]


def mask(text: str) -> tuple[str, Counter]:
    """Return the text with secrets replaced, and how many of each kind were found."""
    counts: Counter = Counter()
    for label, pattern in PATTERNS:

        def replace(match: re.Match, label: str = label) -> str:
            counts[label] += 1
            keep = match.groupdict().get("keep") or ""
            return f"{keep}***MASKED-{label}***"

        text = pattern.sub(replace, text)
    return text, counts


def _demo() -> None:
    # Fake values, built at runtime so secret scanners do not flag this file.
    samples = [
        "git push https://x-access-token:" + "ghp_" + "A1b2" * 9 + "@github.com/org/repo",
        "Authorization: Bearer " + "abc123XYZ" * 3,
        "DefaultEndpointsProtocol=https;AccountName=demo;AccountKey=" + "Zm9v" * 8 + "==;",
        "export MODEL_API_KEY=" + "sk" + "9" * 20,
        "Server=db;User Id=app;Password=" + "Hunter2" + "!x;",
        "Committed by someone@example.com",
        "MODEL_API_KEY: ***   <- already masked by GitHub, left alone",
        "MODEL_API_KEY: \nlint-and-test   <- empty value: the next line must not be masked",
    ]
    for line in samples:
        masked, _ = mask(line)
        print(f"before: {line}\nafter:  {masked}\n")


if __name__ == "__main__":
    if sys.argv[1:] == ["--demo"]:
        _demo()
    elif len(sys.argv) == 2:
        with open(sys.argv[1], encoding="utf-8") as f:
            masked_text, found = mask(f.read())
        print(masked_text)
        print(f"\n--- masked: {dict(found) or 'nothing found'}", file=sys.stderr)
    else:
        sys.exit(__doc__)
