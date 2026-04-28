"""
Music Recommender — CLI entry point with agentic planning.

Usage:
  python -m src.main                           # interactive agent mode (default)
  python -m src.main --query "study music"    # one-shot natural-language query
  python -m src.main --batch                   # original batch simulation (no API key needed)

Setup:
  pip install -r requirements.txt
  set GEMINI_API_KEY=<your key>    # Windows CMD
  export GEMINI_API_KEY=<your key> # macOS / Linux / Git Bash

  Get a free API key (no credit card) at: https://aistudio.google.com/apikey

Interactive and --query modes call the Gemini API (free tier); --batch runs entirely offline.
"""

import argparse
import os
import sys

from .agent import run_agent
from .logger import get_logger
from .recommender import load_songs, recommend_songs

logger = get_logger("main")

DIVIDER = "─" * 52


# ── display helpers ──────────────────────────────────────────────────────────

def _print_batch_recommendations(recommendations: list) -> None:
    print(f"\n{'Top Recommendations':^52}")
    print(DIVIDER)
    for rank, (song, score, reasons) in enumerate(recommendations, start=1):
        print(f"  #{rank}  {song['title']}")
        print(f"       Artist : {song['artist']}")
        print(f"       Score  : {score:.2f}")
        print(f"       Why    :")
        for reason in reasons:
            print(f"                • {reason}")
        print()
    print(DIVIDER)


def _print_agent_recommendations(recs: list) -> None:
    print(f"\n{'Top Recommendations':^52}")
    print(DIVIDER)
    for rank, song in enumerate(recs, start=1):
        print(f"  #{rank}  {song['title']}")
        print(f"       Artist : {song['artist']}")
        print(f"       Genre  : {song['genre']}  |  Mood: {song['mood']}")
        print(f"       Score  : {song['score']:.2f}")
        print(f"       Why    :")
        for reason in song.get("reasons", []):
            print(f"                • {reason}")
        print()
    print(DIVIDER)


def _check_api_key() -> bool:
    if not os.environ.get("GEMINI_API_KEY"):
        print("ERROR: GEMINI_API_KEY is not set.")
        print("  Get a free key at: https://aistudio.google.com/apikey")
        print("  Windows CMD : set GEMINI_API_KEY=<your key>")
        print("  macOS/Linux : export GEMINI_API_KEY=<your key>")
        logger.error("GEMINI_API_KEY not set — cannot start agent")
        return False
    return True


# ── modes ─────────────────────────────────────────────────────────────────────

def run_interactive() -> None:
    """Agent-powered interactive REPL: describe what you want, get recommendations."""
    if not _check_api_key():
        sys.exit(1)

    print("\nMusic Recommendation Agent")
    print("Describe what you want to listen to, or type 'quit' to exit.")
    print(DIVIDER)
    logger.info("Interactive session started")

    while True:
        try:
            query = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            logger.info("Interactive session ended by interrupt")
            return

        if not query:
            continue
        if query.lower() in {"quit", "exit", "q"}:
            print("Goodbye!")
            logger.info("Interactive session ended")
            return

        logger.info("Interactive query: %r", query)
        print("\nPlanning and fetching recommendations...")

        try:
            result = run_agent(query)
        except Exception as exc:
            logger.error("Agent error: %s", exc, exc_info=True)
            print(f"\nError: {exc}")
            continue

        if result["plan_steps"]:
            print(f"\n{DIVIDER}")
            print("Planning steps taken:")
            for i, step in enumerate(result["plan_steps"], 1):
                print(f"  {i}. {step}")

        if result["recommendations"]:
            _print_agent_recommendations(result["recommendations"])

        print(f"\nAgent: {result['response']}")


def run_single_query(query: str) -> None:
    """One-shot agent query from the command line."""
    if not _check_api_key():
        sys.exit(1)

    logger.info("One-shot query: %r", query)
    print(f"\nQuery: {query}")
    print("Planning and fetching recommendations...")

    try:
        result = run_agent(query)
    except Exception as exc:
        logger.error("Agent error: %s", exc, exc_info=True)
        print(f"\nError: {exc}")
        sys.exit(1)

    if result["plan_steps"]:
        print(f"\n{DIVIDER}")
        print("Planning steps taken:")
        for i, step in enumerate(result["plan_steps"], 1):
            print(f"  {i}. {step}")

    if result["recommendations"]:
        _print_agent_recommendations(result["recommendations"])

    print(f"\nAgent: {result['response']}")


def run_batch() -> None:
    """Original batch simulation over predefined profiles (no API key required)."""
    logger.info("Batch simulation started")
    songs = load_songs("data/songs.csv")

    profiles = [
        # Standard
        ("High-Energy Pop",          {"favorite_genre": "pop",  "favorite_mood": "happy",     "target_energy": 0.9,  "likes_acoustic": False}),
        ("Chill Lofi",               {"favorite_genre": "lofi", "favorite_mood": "calm",      "target_energy": 0.2,  "likes_acoustic": True}),
        ("Deep Intense Rock",        {"favorite_genre": "rock", "favorite_mood": "angry",     "target_energy": 0.85, "likes_acoustic": False}),
        # Adversarial
        ("[ADV] Conflicting Energy+Mood", {"favorite_genre": "pop",   "favorite_mood": "sad",       "target_energy": 0.9,  "likes_acoustic": False}),
        ("[ADV] Impossible Genre",        {"favorite_genre": "k-pop", "favorite_mood": "happy",     "target_energy": 0.5,  "likes_acoustic": False}),
        ("[ADV] Neutral Energy (0.5)",    {"favorite_genre": "rock",  "favorite_mood": "angry",     "target_energy": 0.5,  "likes_acoustic": False}),
        ("[ADV] Acoustic+EDM Mismatch",   {"favorite_genre": "edm",   "favorite_mood": "energetic", "target_energy": 0.95, "likes_acoustic": True}),
        ("[ADV] Perfect-Score Bait",      {"favorite_genre": "pop",   "favorite_mood": "happy",     "target_energy": 1.0,  "likes_acoustic": True}),
    ]

    for label, user_prefs in profiles:
        logger.info("Batch profile: %s", label)
        print(f"\n{'=' * 52}")
        print(f"  Profile: {label}")
        print(f"{'=' * 52}")
        try:
            recs = recommend_songs(user_prefs, songs, k=5)
            _print_batch_recommendations(recs)
        except Exception as exc:
            logger.error("Batch profile %r failed: %s", label, exc, exc_info=True)
            print(f"  Error: {exc}")

    logger.info("Batch simulation complete")


# ── entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Music Recommender with agentic planning",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  python -m src.main\n"
            "  python -m src.main --query 'chill music for studying'\n"
            "  python -m src.main --batch"
        ),
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--batch", action="store_true",
        help="run batch simulation over preset profiles (no API key needed)",
    )
    group.add_argument(
        "--query", metavar="TEXT",
        help="one-shot natural-language query to the agent",
    )
    args = parser.parse_args()

    if args.batch:
        run_batch()
    elif args.query:
        run_single_query(args.query)
    else:
        run_interactive()


if __name__ == "__main__":
    main()
