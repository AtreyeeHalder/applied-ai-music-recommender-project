"""
Agentic planning loop for the music recommender, powered by Google Gemini (free tier).

Flow: user request → load_catalog tool → get_recommendations tool → synthesized response.
All steps are logged to logs/recommender.log.

Get a free API key (no credit card) at: https://aistudio.google.com/apikey
"""

import json
import os
from typing import Optional

import google.generativeai as genai

from .logger import get_logger
from .recommender import load_songs, recommend_songs

logger = get_logger("agent")

_SYSTEM = """\
You are a music recommendation agent. When given a user request:
1. Call load_catalog to load the database and see available genres and moods.
2. Infer the best-fit genre, mood, energy, and acoustic preference from the request.
   - "chill / study / focus / relax" → energy 0.2–0.4, mood: calm/chill/focused/relaxed
   - "workout / pump up / intense"   → energy 0.8–1.0, mood: intense/energetic/angry
   - "party / dance / happy"         → energy 0.7–0.9, mood: happy/energetic
   - "sad / heartbreak / melancholy" → energy 0.2–0.5, mood: sad/moody
   If the user's genre is absent from the catalog, pick the closest one and mention it.
3. Call get_recommendations with the inferred profile.
4. Reply with a warm, concise paragraph explaining your top picks and why they fit.
"""


# ── tool stubs — Gemini introspects type hints and docstrings for the schema ──

def load_catalog(csv_path: str = "data/songs.csv") -> dict:
    """Load the song catalog from a CSV file. Call this first to discover available genres and moods before recommending."""
    pass  # intercepted in the agent loop; never actually called


def get_recommendations(
    favorite_genre: str,
    favorite_mood: str,
    target_energy: float,
    likes_acoustic: bool,
    k: int = 5,
) -> dict:
    """Score all songs against a user profile and return the top k matches with scores and explanations. Use genres and moods returned by load_catalog."""
    pass  # intercepted in the agent loop; never actually called


# ── main agent loop ───────────────────────────────────────────────────────────

def run_agent(user_request: str, songs_cache: Optional[list] = None) -> dict:
    """
    Run the agentic planning loop for a natural-language music request.

    Returns:
        {
          "response":        str,        # agent's final message to the user
          "recommendations": list[dict], # scored songs
          "plan_steps":      list[str],  # tool calls made (for display)
        }
    """
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    logger.info("Agent started | request=%r", user_request)

    catalog: Optional[list] = songs_cache
    recommendations: list = []
    plan_steps: list = []

    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        tools=[load_catalog, get_recommendations],
        system_instruction=_SYSTEM,
    )
    chat = model.start_chat(enable_automatic_function_calling=False)
    response = chat.send_message(user_request)

    for iteration in range(6):
        logger.debug("Iteration %d", iteration + 1)

        fn_calls = [
            p.function_call
            for p in response.parts
            if p.function_call and p.function_call.name
        ]

        if not fn_calls:
            text = response.text
            logger.info(
                "Agent done | steps=%d | recs=%d", len(plan_steps), len(recommendations)
            )
            return {
                "response": text,
                "recommendations": recommendations,
                "plan_steps": plan_steps,
            }

        tool_responses = []
        for fc in fn_calls:
            name = fc.name
            args = dict(fc.args)
            plan_steps.append(f"[{name}] {json.dumps(args)}")
            logger.info("Tool call: %s | %s", name, args)

            try:
                raw = _execute_tool(name, args, catalog)
                if name == "load_catalog":
                    catalog = raw.pop("_catalog")
                elif name == "get_recommendations":
                    recommendations = raw.get("recommendations", [])
                tool_responses.append(
                    genai.protos.Part(
                        function_response=genai.protos.FunctionResponse(
                            name=name, response={"result": raw}
                        )
                    )
                )
            except Exception as exc:
                logger.error("Tool %s failed: %s", name, exc, exc_info=True)
                tool_responses.append(
                    genai.protos.Part(
                        function_response=genai.protos.FunctionResponse(
                            name=name, response={"error": str(exc)}
                        )
                    )
                )

        response = chat.send_message(tool_responses)

    logger.warning("Agent exhausted iteration limit without completing")
    return {
        "response": "Sorry, I couldn't complete the request in time.",
        "recommendations": recommendations,
        "plan_steps": plan_steps,
    }


def _execute_tool(name: str, inputs: dict, catalog: Optional[list]) -> dict:
    """Dispatch a tool call and return the result dict."""
    if name == "load_catalog":
        if catalog is not None:
            songs = catalog
            logger.debug("Using pre-loaded catalog (%d songs)", len(songs))
        else:
            path = inputs.get("csv_path", "data/songs.csv")
            songs = load_songs(path)
        genres = sorted(set(s["genre"] for s in songs))
        moods = sorted(set(s["mood"] for s in songs))
        logger.info(
            "Catalog ready: %d songs | genres=%s | moods=%s", len(songs), genres, moods
        )
        return {
            "status": "ok",
            "song_count": len(songs),
            "genres": genres,
            "moods": moods,
            "_catalog": songs,  # stripped by caller before sending to model
        }

    if name == "get_recommendations":
        if catalog is None:
            raise ValueError("Catalog not loaded — call load_catalog first")
        prefs = {
            "favorite_genre": inputs["favorite_genre"],
            "favorite_mood": inputs["favorite_mood"],
            "target_energy": float(inputs["target_energy"]),
            "likes_acoustic": bool(inputs["likes_acoustic"]),
        }
        k = int(inputs.get("k", 5))
        recs = recommend_songs(prefs, catalog, k=k)
        logger.info("Recommendations computed: top %d for prefs=%s", k, prefs)
        return {
            "recommendations": [
                {
                    "title": s["title"],
                    "artist": s["artist"],
                    "genre": s["genre"],
                    "mood": s["mood"],
                    "energy": s["energy"],
                    "score": score,
                    "reasons": reasons,
                }
                for s, score, reasons in recs
            ]
        }

    raise ValueError(f"Unknown tool: {name!r}")
