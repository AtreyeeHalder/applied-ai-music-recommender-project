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
pytest
```

---

## Sample Interactions

### Example 1

**Input:**
```
[Sample user input or query]
```

**Output:**
```
[Resulting AI output]
```

---

### Example 2

**Input:**
```
[Sample user input or query]
```

**Output:**
```
[Resulting AI output]
```

---

### Example 3

**Input:**
```
[Sample user input or query]
```

**Output:**
```
[Resulting AI output]
```

---

## Design Decisions

[Why you built it this way — explain the key architectural and technical choices you made. What trade-offs did you consider? What alternatives did you rule out and why?]

| Decision | Rationale | Trade-off |
|----------|-----------|-----------|
| [Decision 1] | [Why] | [What was sacrificed] |
| [Decision 2] | [Why] | [What was sacrificed] |
| [Decision 3] | [Why] | [What was sacrificed] |

---

## Testing Summary

### What Worked

- [Finding 1]
- [Finding 2]

### What Didn't

- [Challenge 1]
- [Challenge 2]

### What You Learned

[Key takeaways from the testing process — surprises, limitations you discovered, and insights that would inform a future version.]

---

## Reflection

[What this project taught you about AI and problem-solving. How did your understanding of AI systems change? What would you do differently? What excites you about where this could go?]

---

## Acknowledgments

- [CodePath AI 110 — Spring 2026]
- [Any libraries, APIs, or resources used]
