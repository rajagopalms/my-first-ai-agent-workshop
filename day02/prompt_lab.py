"""Day 2, part 1: see what the system message, temperature and max_tokens do.

Runs three small experiments and prints the answers side by side:
  1. system   - the same question with a vague and a precise system message
  2. temp     - the same question at temperature 0 and 1.2, twice each
  3. tokens   - the same question with max_tokens 400 and 30

Usage:
    python day02/prompt_lab.py            # all three
    python day02/prompt_lab.py temp       # just one
"""

import sys

from llm import chat


def show(label: str, reply) -> None:
    print(f"\n[{label}]\n{reply.text}\n  -> {reply.usage_line()}")


def experiment_system() -> None:
    print("\n=== 1. System message: context changes the meaning ===")
    question = "In 2 sentences: what is a token?"
    vague = "You are a helpful assistant for a DevOps engineer."
    precise = (
        "You teach large language model (LLM) concepts to a DevOps engineer. "
        "Here 'token' always means the unit an LLM reads and is billed by, "
        "never an authentication token. Use one DevOps analogy."
    )
    show("vague system message", chat(vague, question))
    show("precise system message", chat(precise, question))


def experiment_temperature() -> None:
    print("\n=== 2. Temperature: 0 = repeatable, high = varied ===")
    system = "You name things. Reply with the name only."
    question = "Suggest a name for a CI pipeline that deploys a web app."
    for temperature in (0.0, 1.2):
        for attempt in (1, 2):
            show(f"temperature {temperature}, run {attempt}", chat(system, question, temperature=temperature))


def experiment_max_tokens() -> None:
    print("\n=== 3. max_tokens: a hard cap on the answer length ===")
    system = "You explain DevOps topics clearly."
    question = "Explain what a CI pipeline does, step by step."
    show("max_tokens 400", chat(system, question, max_tokens=400))
    show("max_tokens 30 (watch finish: length)", chat(system, question, max_tokens=30))


EXPERIMENTS = {
    "system": experiment_system,
    "temp": experiment_temperature,
    "tokens": experiment_max_tokens,
}

if __name__ == "__main__":
    chosen = sys.argv[1:] or list(EXPERIMENTS)
    for name in chosen:
        if name not in EXPERIMENTS:
            sys.exit(f"Unknown experiment {name!r}. Pick from: {', '.join(EXPERIMENTS)}")
        EXPERIMENTS[name]()
