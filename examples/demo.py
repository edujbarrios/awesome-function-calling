"""
examples/demo.py
----------------
Beginner-friendly demonstration of the awesome-function-calling catalog.

Run from the repository root:
    python examples/demo.py
"""

import sys
from pathlib import Path

# Allow running from the examples/ folder without installing the package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from llm_placeholder import load_functions, run  # noqa: E402


def list_all_functions() -> None:
    """Print a formatted table of every function in the catalog."""
    functions = load_functions()
    print(f"\n  {'NAME':<22} DESCRIPTION")
    print("  " + "─" * 70)
    for fn in functions:
        name = fn["name"]
        desc = fn["description"]
        # Truncate long descriptions for display
        if len(desc) > 55:
            desc = desc[:52] + "..."
        print(f"  {name:<22} {desc}")
    print(f"\n  Total: {len(functions)} functions loaded from functions/\n")


def run_single(query: str) -> None:
    """Run one query through the mock pipeline and print the result."""
    run(query)


if __name__ == "__main__":
    print("\n" + "=" * 62)
    print("  awesome-function-calling — Examples Demo")
    print("=" * 62)

    # ── Show the full catalog ─────────────────────────────────
    print("\n  [ All loaded functions ]\n")
    list_all_functions()

    # ── Run a handful of representative queries ───────────────
    print("  [ Mock pipeline demos ]\n")
    queries = [
        "What's the weather in Tokyo?",
        "Remind me to call mum at 6 pm",
        "How do I get from Atocha station to Barajas airport?",
        "Summarise this long document for me",
        "What is Tesla's stock price right now?",
    ]
    for q in queries:
        run_single(q)
        print()

    print("=" * 62)
    print("  Done. See src/llm_placeholder.py for the live llm7.io demo.")
    print("=" * 62 + "\n")
