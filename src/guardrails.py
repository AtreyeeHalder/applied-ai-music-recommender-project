"""
Input guardrails for the music recommender agent.

Validates and sanitizes LLM-generated get_recommendations arguments before
they reach the scoring engine. Catches common LLM failure modes:
  - Energy outside [0.0, 1.0]  (LLMs sometimes return 1.5 or negative values)
  - Non-numeric energy          (LLMs occasionally hallucinate strings like "high")
  - Empty genre or mood string  (LLM omits the field or returns whitespace)
  - k <= 0 or k > 50           (nonsensical result-count requests)
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GuardrailResult:
    """Outcome of validating one tool-call input dict."""
    sanitized: dict          # corrected inputs, safe to pass to the tool
    violations: list         # human-readable description of each correction made
    blocked: bool = False    # True if input is unrecoverable (future use)


def validate_recommendation_inputs(inputs: dict) -> GuardrailResult:
    """
    Validate and sanitize get_recommendations tool arguments.

    Every violation is corrected in-place and logged in the returned
    violations list so callers can surface warnings without crashing.
    """
    sanitized = dict(inputs)
    violations: list[str] = []

    # ── target_energy: must be a float in [0.0, 1.0] ──────────────────────────
    raw_energy = sanitized.get("target_energy")
    try:
        energy = float(raw_energy)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        violations.append(
            f"target_energy={raw_energy!r} is not numeric; defaulted to 0.5"
        )
        energy = 0.5

    if energy < 0.0:
        violations.append(
            f"target_energy={energy} is below 0.0; clamped to 0.0"
        )
        energy = 0.0
    elif energy > 1.0:
        violations.append(
            f"target_energy={energy} is above 1.0; clamped to 1.0"
        )
        energy = 1.0

    sanitized["target_energy"] = round(energy, 4)

    # ── favorite_genre: must be a non-empty string ────────────────────────────
    genre = sanitized.get("favorite_genre", "")
    if not isinstance(genre, str) or not genre.strip():
        violations.append(
            f"favorite_genre={genre!r} is empty or missing; defaulted to 'pop'"
        )
        sanitized["favorite_genre"] = "pop"
    else:
        sanitized["favorite_genre"] = genre.strip().lower()

    # ── favorite_mood: must be a non-empty string ─────────────────────────────
    mood = sanitized.get("favorite_mood", "")
    if not isinstance(mood, str) or not mood.strip():
        violations.append(
            f"favorite_mood={mood!r} is empty or missing; defaulted to 'happy'"
        )
        sanitized["favorite_mood"] = "happy"
    else:
        sanitized["favorite_mood"] = mood.strip().lower()

    # ── k: must be a positive integer, max 50 ────────────────────────────────
    raw_k = sanitized.get("k", 5)
    try:
        k = int(raw_k)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        violations.append(
            f"k={raw_k!r} is not an integer; defaulted to 5"
        )
        k = 5

    if k < 1:
        violations.append(f"k={k} is less than 1; clamped to 1")
        k = 1
    elif k > 50:
        violations.append(f"k={k} exceeds maximum 50; clamped to 50")
        k = 50

    sanitized["k"] = k

    return GuardrailResult(sanitized=sanitized, violations=violations)
