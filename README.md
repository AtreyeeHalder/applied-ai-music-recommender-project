# CadenceMatcher 2.0: Agentic AI Music Recommender

> An agentic AI system that translates natural-language listening requests into personalized song recommendations using a multi-step planning loop powered by a local Ollama LLM (llama3.2), with structured error logging across all tool calls and agent iterations.

---

## Original Project (Modules 1–3)

**Project Name:** Music Recommender Simulation (CadenceMatcher 1.0)

CadenceMatcher 1.0 was a rule-based music recommender that scored songs from a static catalog against a user's stated taste profile — including preferred genre, mood, target energy level, and acoustic preference — using a weighted formula that prioritized genre match most heavily, followed by mood, energy similarity, and acousticness. Given a `UserProfile`, the system returned a ranked list of the top five songs with the highest compatibility scores. The project explored how scoring weight choices and dataset composition introduce bias, particularly revealing that high-energy listeners received more accurate recommendations than low-energy listeners due to catalog imbalance.

---

## Title and Summary

**CadenceMatcher 2.0: Agentic AI Music Recommender**

CadenceMatcher 2.0 evolves the original rule-based recommender into a conversational, agentic system: a user describes what they want to hear in plain language ("something chill for studying"), and a local Ollama LLM (llama3.2) interprets that request, plans and executes a sequence of tool calls to load the song catalog and score it against an inferred taste profile, then returns a ranked list of recommendations with natural-language explanations. It solves the friction of form-based music discovery; instead of manually selecting genre, mood, and energy sliders, listeners simply say what they need and the agent handles the translation. CadenceMatcher 2.0 is built for music listeners who want intuitive, transparent recommendations without relying on any external API or subscription service, since the entire agentic loop runs locally.

---

## Architecture Overview

- **Entry point:** All input (natural language queries or CLI flags) enters through `main.py`, which routes to one of two paths.
- **`--batch` path:** A Batch Simulator runs 8 predefined profiles (including adversarial edge cases) directly through the Scoring Engine (`recommender.py`), bypassing the agent and producing ranked output for each profile.
- **`--query` / interactive path:** Runs the Agentic Loop in `agent.py` (up to 6 iterations, powered by Ollama llama3.2 via OpenAI-compatible API):
  - **Tool Call 1 — `load_catalog`:** Reads the 200-song, 10-field CSV catalog and returns available genres and moods.
  - **Tool Call 2 — `get_recommendations`:** Passes the LLM's inferred `UserProfile` into the Scoring Engine.
- **Scoring Engine (`recommender.py`):** Scores every song in the catalog (+1.0 genre match, +1.5 mood match, +3.0 energy proximity, +0.5 acoustic match), sorts by total, and returns the top-k songs with scores and reasons.
- **Final Output:** When the agent reaches `finish_reason = stop`, the LLM synthesizes a natural-language summary. Output includes plan steps taken, top-k recommendations, and the LLM summary paragraph.
- **Observability (`logger.py`):** DEBUG logs to `logs/recommender.log`; WARNING logs to stderr.
- **Testing & human evaluation:** Unit tests (`pytest` on `test_recommender.py`) verify the OOP Recommender; manual batch eval runs `--batch` against adversarial edge cases; a human reviewer checks ranked output for quality.

![System Architecture Diagram](assets/System%20Architecture%20Diagram.png)

---

## Setup Instructions

### Prerequisites

- **Python 3.10+** — [python.org/downloads](https://www.python.org/downloads/)
- **Git** — [git-scm.com](https://git-scm.com/)
- **Ollama** — [ollama.com/download](https://ollama.com/download) *(required for interactive and `--query` modes; not needed for `--batch`)*

> **No API key required.** The agentic loop runs entirely on your local machine via Ollama.

---

### 1. Clone the repository

Works the same on all platforms:

```bash
git clone https://github.com/AtreyeeHalder/applied-ai-music-recommender-project.git
cd applied-ai-music-recommender-project
```

---

### 2. Create and activate a virtual environment

**Windows — Command Prompt (CMD)**
```cmd
python -m venv venv
venv\Scripts\activate
```

**Windows — PowerShell**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
> If you see an execution-policy error, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` first, then activate again.

**macOS / Linux**
```bash
python3 -m venv venv
source venv/bin/activate
```

---

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Start Ollama and pull the model

Open a **separate terminal** and start the Ollama server (if it isn't already running):

**Windows (CMD or PowerShell) / macOS / Linux**
```bash
ollama serve
```

Then, in your original terminal (with the venv active), pull the model:

```bash
ollama pull llama3.2
```

You only need to pull the model once. After that, `ollama serve` is the only step needed before running the project.

> **Optional:** To use a different Ollama model, set the `OLLAMA_MODEL` environment variable before running:
>
> **CMD:** `set OLLAMA_MODEL=mistral`
>
> **PowerShell:** `$env:OLLAMA_MODEL = "mistral"`
>
> **macOS / Linux:** `export OLLAMA_MODEL=mistral`

---

### 5. Run the project

All commands are run from the repository root with the virtual environment active.

**Interactive mode** (conversational REPL — requires Ollama):
```bash
python -m src.main
```

**One-shot query** (requires Ollama):

*CMD / PowerShell / macOS / Linux:*
```bash
python -m src.main --query "something chill for studying"
```

**Batch simulation** (no Ollama needed — runs entirely offline):
```bash
python -m src.main --batch
```

**Run tests:**
```bash
python -m pytest
```

---

## Sample Interactions

### Mode 1 — Batch Simulation

**Input (Windows CMD):**
```cmd
python -m src.main --batch
```

**Output — Standard Profiles:**

![Mode 1 - Screenshot 1](assets/Mode%201%20ss1.png)
![Mode 1 - Screenshot 2](assets/Mode%201%20ss2.png)

**Output — Advanced (Adversarial) Profiles:**

![Mode 1 - Screenshot 3](assets/Mode%201%20ss3.png)
![Mode 1 - Screenshot 4](assets/Mode%201%20ss4.png)

---

### Mode 2 — One-Shot Query

**Input (Windows CMD):**
```cmd
python -m src.main --query "chill music for studying"
```

**Output:**

![Mode 2 - Screenshot 1](assets/Mode%202%20ss1.png)
![Mode 2 - Screenshot 2](assets/Mode%202%20ss2.png)

---

### Mode 3 — Interactive Mode

**Input (Windows CMD):**
```cmd
python -m src.main
```
> When prompted, typed: `happy songs for a party`

**Output:**

![Mode 3 - Screenshot 1](assets/Mode%203%20ss1.png)
![Mode 3 - Screenshot 2](assets/Mode%203%20ss2.png)
![Mode 3 - Screenshot 3](assets/Mode%203%20ss3.png)
![Mode 3 - Screenshot 4](assets/Mode%203%20ss4.png)

---

## Design Decisions

- **Increased size of dataset from 18 to 200:** This was done for improved model accuracy and reduced bias.
- **Included various artists, genres, moods:** Different artists, genres, and moods formed a more diverse dataset.
- **Used an Ollama LLM to power the agentic loop:** Anthropic LLMs requires an API key and are not free of cost. Gemini LLMs requires an API key and account login. An Ollama LLM can be run locally, no account creation required, and is free of cost unless it is a larger project. Thus, Ollama is more accessible to a wider audience.
- **Separated batch mode from the agentic loop:** The `--batch` flag routes directly to the Scoring Engine, bypassing Ollama entirely. This means the core recommender logic can be tested and evaluated offline without requiring the model to be running, which makes development faster and keeps scoring tests deterministic.
- **Weighted energy proximity most heavily in the scoring formula:** Energy is the only continuous field in the scoring formula (vs. binary genre/mood/acoustic matches), so a small mismatch can still yield a decent score. Weighting it at +3.0 — compared to +1.0 for genre and +0.5 for acoustic — reflects that perceived song "feel" (tempo, intensity) has the strongest impact on whether a recommendation actually fits the listener's moment.

---

## Testing Summary

The project was tested through two complementary methods: a pytest suite targeting the scoring engine and recommender logic directly, and a manual batch evaluation running 8 predefined profiles (4 standard, 4 adversarial) through the full pipeline. Throughout all testing, structured error logging via `logger.py` captured every tool call and agent iteration — DEBUG-level events (catalog loads, score computations, agent steps) were written to `logs/recommender.log`, while WARNING-level events (unexpected LLM outputs, missing fields) surfaced directly to stderr, making it straightforward to trace failures back to the specific iteration or tool call where they occurred.

- Scoring math is precise and predictable. All exact-value unit tests passed.
- `explain_recommendation()` always produces output. Even when no attributes matched (genre miss, mood miss, maximum energy difference), the method returned a non-empty explanation string rather than failing.
- `load_songs()` type conversion is reliable. Numeric CSV fields (`id`, `energy`, `tempo_bpm`, etc.) are correctly parsed into `int` and `float` types, not left as strings.
- The agentic loop correctly interprets natural language. Both `--query` and interactive modes successfully translated plain-English requests ("chill music for studying", "happy songs for a party") into valid `UserProfile` fields and returned relevant recommendations.
- However, genre is underweighted relative to energy. The scoring formula gives genre only +1.0 point versus energy's maximum of +3.0. This sometimes felt counterintuitive during manual review.

### What You Learned

The most interesting thing I learned is the different tradeoffs involved in choosing an LLM, balancing between accessibility and capability. I chose Ollama because the GitHub repository is public, so it should be usable and accessible by a more general audience instead of a specialized team. I also learned that human evaluation of the batch output is necessary to make sure everything is intuitive and recommendations make sense. The pytest suite confirmed that the scoring math is right, but it can't detect whether the ranked output actually feels like good music for the stated request.

---

## Reflection

This project mainly taught me how different LLMs have their own advantages and disadvantages, and how significantly my choice of LLM powering the agentic loop changed how users would run this project. When I had initially asked Claude Code to assist me with coding the agentic loop, it had proposed using Anthropic definitively without explanation. After I questioned and discussed with Claude Code about tradeoffs and alternative LLMs, I chose to use Ollama because it was best fit for my situation and context. Thus, my biggest takeaways from this project is to always evaluate tradoffs associated with any tools I am using, and when taking assistance from AI, to always ask for explanations when AI output is unclear to continue maintaining control over my code. I believe that AI coding assistant should be used as tools to generate code quickly, but system design and architecture decisions should be made by humans to design the system according to context, audience and specifications.

---

## Acknowledgments

- **CodePath AI 110 — Spring 2026** — course curriculum, project structure, and module assignments that guided CadenceMatcher 1.0 and 2.0
- **[Ollama](https://ollama.com/)** — local LLM runtime that powers the agentic loop without requiring an API key or internet connection
- **[Meta Llama 3.2](https://ollama.com/library/llama3.2)** (via Ollama) — the open-weight language model used for natural-language query interpretation and response synthesis
- **[openai Python SDK](https://github.com/openai/openai-python)** — used as the OpenAI-compatible client to communicate with the local Ollama server
- **[pandas](https://pandas.pydata.org/)** — CSV catalog loading and data manipulation
- **[pytest](https://docs.pytest.org/)** — unit testing framework for the scoring engine and recommender logic
- **[Claude Code](https://claude.ai/code)** (Anthropic) — AI coding assistant used during development; all design decisions and tradeoffs were reviewed and approved by the author
