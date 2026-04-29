"""
Tests for src/guardrails.py — each test demonstrates a specific before/after
guardrail behavior so the examples are visible in the pytest output.
"""

from src.guardrails import validate_recommendation_inputs


def _valid_base(**overrides) -> dict:
    base = {
        "target_energy": 0.7,
        "favorite_genre": "pop",
        "favorite_mood": "happy",
        "likes_acoustic": False,
        "k": 5,
    }
    base.update(overrides)
    return base


# ── energy clamping ───────────────────────────────────────────────────────────

def test_energy_above_1_clamped():
    # LLM returned 1.5 → guardrail clamps to 1.0
    result = validate_recommendation_inputs(_valid_base(target_energy=1.5))
    assert result.sanitized["target_energy"] == 1.0
    assert any("clamped to 1.0" in v for v in result.violations)


def test_energy_below_0_clamped():
    # LLM returned -0.3 → guardrail clamps to 0.0
    result = validate_recommendation_inputs(_valid_base(target_energy=-0.3))
    assert result.sanitized["target_energy"] == 0.0
    assert any("clamped to 0.0" in v for v in result.violations)


def test_energy_non_numeric_defaulted():
    # LLM hallucinated "very high" → guardrail defaults to 0.5
    result = validate_recommendation_inputs(_valid_base(target_energy="very high"))
    assert result.sanitized["target_energy"] == 0.5
    assert any("not numeric" in v for v in result.violations)


def test_energy_at_boundary_no_violation():
    # Exactly 1.0 is valid — no violation expected
    result = validate_recommendation_inputs(_valid_base(target_energy=1.0))
    energy_violations = [v for v in result.violations if "energy" in v]
    assert energy_violations == []
    assert result.sanitized["target_energy"] == 1.0


def test_energy_at_zero_no_violation():
    # Exactly 0.0 is valid — no violation expected
    result = validate_recommendation_inputs(_valid_base(target_energy=0.0))
    energy_violations = [v for v in result.violations if "energy" in v]
    assert energy_violations == []


# ── genre validation ──────────────────────────────────────────────────────────

def test_empty_genre_defaulted():
    # LLM returned "" → guardrail defaults to "pop"
    result = validate_recommendation_inputs(_valid_base(favorite_genre=""))
    assert result.sanitized["favorite_genre"] == "pop"
    assert any("defaulted to 'pop'" in v for v in result.violations)


def test_whitespace_genre_defaulted():
    # LLM returned "   " → treated as empty
    result = validate_recommendation_inputs(_valid_base(favorite_genre="   "))
    assert result.sanitized["favorite_genre"] == "pop"
    assert any("defaulted to 'pop'" in v for v in result.violations)


def test_genre_case_normalized():
    # LLM returned "Rock" → normalized to "rock" (no violation)
    result = validate_recommendation_inputs(_valid_base(favorite_genre="Rock"))
    assert result.sanitized["favorite_genre"] == "rock"
    genre_violations = [v for v in result.violations if "genre" in v]
    assert genre_violations == []


# ── mood validation ───────────────────────────────────────────────────────────

def test_empty_mood_defaulted():
    # LLM returned "" → guardrail defaults to "happy"
    result = validate_recommendation_inputs(_valid_base(favorite_mood=""))
    assert result.sanitized["favorite_mood"] == "happy"
    assert any("defaulted to 'happy'" in v for v in result.violations)


def test_mood_case_normalized():
    # LLM returned "HAPPY" → normalized to "happy" (no violation)
    result = validate_recommendation_inputs(_valid_base(favorite_mood="HAPPY"))
    assert result.sanitized["favorite_mood"] == "happy"
    mood_violations = [v for v in result.violations if "mood" in v]
    assert mood_violations == []


# ── k validation ──────────────────────────────────────────────────────────────

def test_k_zero_clamped_to_one():
    # LLM returned k=0 → guardrail clamps to 1
    result = validate_recommendation_inputs(_valid_base(k=0))
    assert result.sanitized["k"] == 1
    assert any("clamped to 1" in v for v in result.violations)


def test_k_negative_clamped_to_one():
    # LLM returned k=-5 → guardrail clamps to 1
    result = validate_recommendation_inputs(_valid_base(k=-5))
    assert result.sanitized["k"] == 1
    assert any("clamped to 1" in v for v in result.violations)


def test_k_too_large_clamped():
    # LLM returned k=999 → guardrail clamps to 50
    result = validate_recommendation_inputs(_valid_base(k=999))
    assert result.sanitized["k"] == 50
    assert any("clamped to 50" in v for v in result.violations)


def test_k_non_integer_defaulted():
    # LLM returned k="many" → defaulted to 5
    result = validate_recommendation_inputs(_valid_base(k="many"))
    assert result.sanitized["k"] == 5
    assert any("not an integer" in v for v in result.violations)


# ── clean input produces no violations ────────────────────────────────────────

def test_valid_input_no_violations():
    # A well-formed input should pass through with zero violations
    result = validate_recommendation_inputs(_valid_base())
    assert result.violations == []
    assert result.blocked is False


def test_valid_input_values_preserved():
    # Values should be unchanged (modulo string normalization)
    inputs = _valid_base(target_energy=0.6, favorite_genre="lofi", favorite_mood="chill", k=3)
    result = validate_recommendation_inputs(inputs)
    assert result.sanitized["target_energy"] == 0.6
    assert result.sanitized["favorite_genre"] == "lofi"
    assert result.sanitized["favorite_mood"] == "chill"
    assert result.sanitized["k"] == 3


# ── multiple violations in one call ───────────────────────────────────────────

def test_multiple_violations_reported():
    # Energy out of range AND empty genre → both violations logged
    bad = {
        "target_energy": 2.0,
        "favorite_genre": "",
        "favorite_mood": "happy",
        "likes_acoustic": False,
        "k": 5,
    }
    result = validate_recommendation_inputs(bad)
    assert len(result.violations) >= 2
    assert result.sanitized["target_energy"] == 1.0
    assert result.sanitized["favorite_genre"] == "pop"
