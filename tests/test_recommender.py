from src.recommender import Song, UserProfile, Recommender, score_song, load_songs
import os
import tempfile


def make_song(**kwargs) -> Song:
    defaults = dict(
        id=1,
        title="Test Track",
        artist="Test Artist",
        genre="pop",
        mood="happy",
        energy=0.8,
        tempo_bpm=120,
        valence=0.9,
        danceability=0.8,
        acousticness=0.2,
    )
    defaults.update(kwargs)
    return Song(**defaults)


def make_user(**kwargs) -> UserProfile:
    defaults = dict(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    defaults.update(kwargs)
    return UserProfile(**defaults)


def make_small_recommender() -> Recommender:
    songs = [
        make_song(id=1, title="Test Pop Track", genre="pop", mood="happy", energy=0.8, acousticness=0.2),
        make_song(id=2, title="Chill Lofi Loop", genre="lofi", mood="chill", energy=0.4, acousticness=0.9),
    ]
    return Recommender(songs)


# ── original tests ────────────────────────────────────────────────────────────

def test_recommend_returns_songs_sorted_by_score():
    user = make_user()
    rec = make_small_recommender()
    results = rec.recommend(user, k=2)

    assert len(results) == 2
    assert results[0].genre == "pop"
    assert results[0].mood == "happy"


def test_explain_recommendation_returns_non_empty_string():
    user = make_user()
    rec = make_small_recommender()
    song = rec.songs[0]

    explanation = rec.explain_recommendation(user, song)
    assert isinstance(explanation, str)
    assert explanation.strip() != ""


# ── score_song: exact values ──────────────────────────────────────────────────

def test_score_perfect_match():
    # genre +1.0, mood +1.5, energy diff=0 so +3.0, acoustic skipped → 5.5
    user = dict(favorite_genre="pop", favorite_mood="happy", target_energy=0.8, likes_acoustic=False)
    song = dict(genre="pop", mood="happy", energy=0.8, acousticness=0.2)
    score, _ = score_song(user, song)
    assert score == 5.5


def test_score_acoustic_bonus_applied():
    # genre +1.0, mood +1.5, energy diff=0 → +3.0, acoustic +0.5 → 6.0
    user = dict(favorite_genre="pop", favorite_mood="happy", target_energy=0.8, likes_acoustic=True)
    song = dict(genre="pop", mood="happy", energy=0.8, acousticness=0.8)
    score, _ = score_song(user, song)
    assert score == 6.0


def test_score_acoustic_bonus_not_applied_when_low_acousticness():
    # likes_acoustic=True but acousticness=0.2 (< 0.5) → no bonus
    user = dict(favorite_genre="pop", favorite_mood="happy", target_energy=0.8, likes_acoustic=True)
    song = dict(genre="pop", mood="happy", energy=0.8, acousticness=0.2)
    score, _ = score_song(user, song)
    assert score == 5.5


def test_score_acoustic_bonus_not_applied_when_user_dislikes_acoustic():
    # high acousticness song but user doesn't want acoustic → no bonus
    user = dict(favorite_genre="pop", favorite_mood="happy", target_energy=0.8, likes_acoustic=False)
    song = dict(genre="pop", mood="happy", energy=0.8, acousticness=0.9)
    score, _ = score_song(user, song)
    assert score == 5.5


def test_score_no_genre_match():
    # genre miss: -1.0 vs perfect → score 4.5
    user = dict(favorite_genre="pop", favorite_mood="happy", target_energy=0.8, likes_acoustic=False)
    song = dict(genre="rock", mood="happy", energy=0.8, acousticness=0.2)
    score, _ = score_song(user, song)
    assert score == 4.5


def test_score_no_mood_match():
    # mood miss: -1.5 vs perfect → score 4.0
    user = dict(favorite_genre="pop", favorite_mood="happy", target_energy=0.8, likes_acoustic=False)
    song = dict(genre="pop", mood="sad", energy=0.8, acousticness=0.2)
    score, _ = score_song(user, song)
    assert score == 4.0


def test_score_maximum_energy_diff():
    # energy diff = 1.0 → energy points = 0.0
    user = dict(favorite_genre="pop", favorite_mood="happy", target_energy=0.0, likes_acoustic=False)
    song = dict(genre="pop", mood="happy", energy=1.0, acousticness=0.2)
    score, _ = score_song(user, song)
    assert score == 2.5  # genre +1.0, mood +1.5, energy +0.0


def test_score_reasons_list_contents():
    user = dict(favorite_genre="pop", favorite_mood="happy", target_energy=0.8, likes_acoustic=True)
    song = dict(genre="pop", mood="happy", energy=0.8, acousticness=0.8)
    _, reasons = score_song(user, song)
    assert any("genre" in r for r in reasons)
    assert any("mood" in r for r in reasons)
    assert any("energy" in r for r in reasons)
    assert any("acoustic" in r for r in reasons)


# ── Recommender.recommend ─────────────────────────────────────────────────────

def test_recommend_k_larger_than_catalog():
    # k=10 with only 2 songs → should return all 2, not crash
    rec = make_small_recommender()
    results = rec.recommend(make_user(), k=10)
    assert len(results) == 2


def test_recommend_k_equals_one():
    rec = make_small_recommender()
    results = rec.recommend(make_user(), k=1)
    assert len(results) == 1
    assert results[0].genre == "pop"


def test_recommend_lower_score_song_ranked_second():
    rec = make_small_recommender()
    results = rec.recommend(make_user(favorite_genre="pop", favorite_mood="happy"), k=2)
    assert results[1].genre == "lofi"


def test_recommend_single_song_catalog():
    rec = Recommender([make_song()])
    results = rec.recommend(make_user(), k=5)
    assert len(results) == 1


def test_recommend_empty_catalog():
    rec = Recommender([])
    results = rec.recommend(make_user(), k=5)
    assert results == []


# ── Recommender.explain_recommendation ───────────────────────────────────────

def test_explain_contains_score():
    rec = make_small_recommender()
    explanation = rec.explain_recommendation(make_user(), rec.songs[0])
    assert "Score:" in explanation


def test_explain_no_matches_fallback():
    # genre and mood both miss, energy diff = 1.0 → score 0.0, reasons should still be non-empty
    user = make_user(favorite_genre="jazz", favorite_mood="sad", target_energy=0.0, likes_acoustic=False)
    song = make_song(genre="pop", mood="happy", energy=1.0, acousticness=0.1)
    rec = Recommender([song])
    explanation = rec.explain_recommendation(user, song)
    assert isinstance(explanation, str)
    assert explanation.strip() != ""


# ── edge cases: conflicting / adversarial profiles ────────────────────────────

def test_conflicting_mood_and_energy():
    # sad mood but very high energy target — should not crash, just score both
    songs = [
        make_song(id=1, genre="pop", mood="sad", energy=0.9),
        make_song(id=2, genre="pop", mood="happy", energy=0.3),
    ]
    rec = Recommender(songs)
    user = make_user(favorite_mood="sad", target_energy=0.9)
    results = rec.recommend(user, k=2)
    assert len(results) == 2


def test_impossible_genre_still_returns_results():
    # user wants a genre not in the catalog → all songs miss on genre, still get ranked
    rec = make_small_recommender()
    user = make_user(favorite_genre="k-pop")
    results = rec.recommend(user, k=2)
    assert len(results) == 2


def test_neutral_energy_midpoint():
    # target_energy=0.5, song energy=0.5 → energy diff=0.0 → full +3.0
    user = dict(favorite_genre="pop", favorite_mood="happy", target_energy=0.5, likes_acoustic=False)
    song = dict(genre="pop", mood="happy", energy=0.5, acousticness=0.2)
    score, _ = score_song(user, song)
    assert score == 5.5


def test_acoustic_edm_mismatch():
    # user wants acoustic but song is EDM (very low acousticness) → no bonus
    user = dict(favorite_genre="edm", favorite_mood="energetic", target_energy=0.95, likes_acoustic=True)
    song = dict(genre="edm", mood="energetic", energy=0.95, acousticness=0.05)
    score, _ = score_song(user, song)
    assert score == 5.5  # genre+mood+energy, no acoustic bonus


# ── load_songs ────────────────────────────────────────────────────────────────

def test_load_songs_returns_correct_types():
    content = (
        "id,title,artist,genre,mood,energy,tempo_bpm,valence,danceability,acousticness\n"
        "1,Test Song,Test Artist,pop,happy,0.8,120,0.9,0.8,0.2\n"
    )
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write(content)
        path = f.name

    try:
        songs = load_songs(path)
        assert len(songs) == 1
        s = songs[0]
        assert isinstance(s["id"], int)
        assert isinstance(s["energy"], float)
        assert isinstance(s["title"], str)
    finally:
        os.unlink(path)


def test_load_songs_multiple_rows():
    content = (
        "id,title,artist,genre,mood,energy,tempo_bpm,valence,danceability,acousticness\n"
        "1,Song A,Artist A,pop,happy,0.8,120,0.9,0.8,0.2\n"
        "2,Song B,Artist B,rock,angry,0.9,140,0.5,0.7,0.1\n"
        "3,Song C,Artist C,lofi,chill,0.3,80,0.6,0.4,0.8\n"
    )
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write(content)
        path = f.name

    try:
        songs = load_songs(path)
        assert len(songs) == 3
        assert songs[1]["genre"] == "rock"
    finally:
        os.unlink(path)
