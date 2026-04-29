"""
Agentic planning loop for the music recommender, powered by Ollama (local, free).

Flow: user request → load_catalog tool → get_recommendations tool → synthesized response.
All steps are logged to logs/recommender.log.

Setup:
  1. Install Ollama: https://ollama.com/download
  2. Pull a model: ollama pull llama3.2
  3. No API key needed — runs entirely on your machine.
"""

import json
import os
from typing import Optional

from openai import OpenAI

from .guardrails import validate_recommendation_inputs
from .logger import get_logger
from .recommender import load_songs, recommend_songs

logger = get_logger("agent")

OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")

_client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",  # required by the library but not used by Ollama
)

_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "load_catalog",
            "description": (
                "Load the song catalog from a CSV file. "
                "Call this first to discover available genres and moods before recommending."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "csv_path": {
                        "type": "string",
                        "description": "Path to songs CSV (default: data/songs.csv)",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_recommendations",
            "description": (
                "Score all songs against a user profile and return the top k matches "
                "with scores and explanations. Use genres and moods returned by load_catalog."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "favorite_genre": {
                        "type": "string",
                        "description": "User's preferred genre (must exist in catalog)",
                    },
                    "favorite_mood": {
                        "type": "string",
                        "description": "User's preferred mood (must exist in catalog)",
                    },
                    "target_energy": {
                        "type": "number",
                        "description": "Target energy 0.0 (very calm) to 1.0 (very intense)",
                    },
                    "likes_acoustic": {
                        "type": "boolean",
                        "description": "True if user prefers acoustic-sounding songs",
                    },
                    "k": {
                        "type": "integer",
                        "description": "Number of songs to return (default: 5)",
                    },
                },
                "required": [
                    "favorite_genre",
                    "favorite_mood",
                    "target_energy",
                    "likes_acoustic",
                ],
            },
        },
    },
]

_SYSTEM = """\
You are a music recommendation agent. When given a user request:
1. Call load_catalog to load the database and see available genres and moods.
2. Infer the best-fit genre, mood, energy, and acoustic preference from the request.
   - "chill / study / focus / relax" -> energy 0.2-0.4, mood: calm/chill/focused/relaxed
   - "workout / pump up / intense"   -> energy 0.8-1.0, mood: intense/energetic/angry
   - "party / dance / happy"         -> energy 0.7-0.9, mood: happy/energetic
   - "sad / heartbreak / melancholy" -> energy 0.2-0.5, mood: sad/moody
   If the user's genre is absent from the catalog, pick the closest one and mention it.
3. Call get_recommendations with the inferred profile.
4. Reply with a warm, concise paragraph explaining your top picks and why they fit.
"""


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
    logger.info("Agent started | request=%r", user_request)

    catalog: Optional[list] = songs_cache or load_songs("data/songs.csv")
    recommendations: list = []
    plan_steps: list = []
    messages = [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": user_request},
    ]

    for iteration in range(6):
        logger.debug("Iteration %d | messages=%d", iteration + 1, len(messages))

        response = _client.chat.completions.create(
            model=OLLAMA_MODEL,
            messages=messages,
            tools=_TOOLS,
        )

        choice = response.choices[0]
        finish_reason = choice.finish_reason
        message = choice.message
        logger.debug("finish_reason=%s", finish_reason)

        if finish_reason == "stop":
            text = message.content or ""
            logger.info(
                "Agent done | steps=%d | recs=%d", len(plan_steps), len(recommendations)
            )
            return {
                "response": text,
                "recommendations": recommendations,
                "plan_steps": plan_steps,
            }

        if finish_reason != "tool_calls" or not message.tool_calls:
            logger.warning("Unexpected finish_reason: %s", finish_reason)
            break

        messages.append(message)

        for tool_call in message.tool_calls:
            name = tool_call.function.name
            inputs = json.loads(tool_call.function.arguments)

            plan_steps.append(f"[{name}] {json.dumps(inputs)}")
            logger.info("Tool call: %s | input=%s", name, inputs)

            try:
                raw = _execute_tool(name, inputs, catalog)
                if name == "load_catalog":
                    catalog = raw.pop("_catalog")
                elif name == "get_recommendations":
                    recommendations = raw.get("recommendations", [])
                content = json.dumps(raw)
            except Exception as exc:
                logger.error("Tool %s failed: %s", name, exc, exc_info=True)
                content = json.dumps({"error": str(exc)})

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": content,
            })

    logger.warning("Agent exhausted iteration limit without completing")
    return {
        "response": "Sorry, I couldn't complete the request in time.",
        "recommendations": recommendations,
        "plan_steps": plan_steps,
    }


def _parse_energy(value) -> float:
    """Accept a float or a range string like '0.4-0.6' (local models sometimes return ranges)."""
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    if "-" in s:
        parts = s.split("-")
        return (float(parts[0]) + float(parts[1])) / 2
    return float(s)


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
            "_catalog": songs,
        }

    if name == "get_recommendations":
        if catalog is None:
            raise ValueError("Catalog not loaded — call load_catalog first")
        guard = validate_recommendation_inputs(inputs)
        for violation in guard.violations:
            logger.warning("Guardrail: %s", violation)
        inputs = guard.sanitized
        prefs = {
            "favorite_genre": inputs["favorite_genre"],
            "favorite_mood": inputs["favorite_mood"],
            "target_energy": _parse_energy(inputs["target_energy"]),
            "likes_acoustic": bool(inputs["likes_acoustic"]),
        }
        k = int(inputs.get("k", 5))
        recs = recommend_songs(prefs, catalog, k=k)
        logger.info("Recommendations computed: top %d for prefs=%s", k, prefs)
        result: dict = {
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
        if guard.violations:
            result["guardrail_warnings"] = guard.violations
        return result

    raise ValueError(f"Unknown tool: {name!r}")
