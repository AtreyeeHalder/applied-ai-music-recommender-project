# Model Card: CadenceMatcher 2.0 — Reflection and Ethics

---

## Limitations and Biases

**Scoring imbalance:** The scoring formula weights energy proximity at up to +3.0 points versus only +1.0 for genre match and +1.5 for mood. In practice, this means two songs in completely different genres can outscore a genre-matched song if their energy levels are closer to the user's target. During manual batch evaluation, this felt counterintuitive — a user asking for "hip-hop" could receive an ambient song ranked above a hip-hop track simply because its energy happened to be closer to 0.6.

**Catalog bias toward Western, English-language music:** Even at 200 songs, the catalog does not represent global music tastes. Genres like K-pop, reggae, Afrobeats, and blues are absent or underrepresented. A user whose preferred genre is not in the catalog will receive a substituted genre recommendation, which the system notes — but the underlying issue is that certain listeners are structurally disadvantaged from the start.

**LLM inference variability:** Because the agentic loop depends on a local LLM (llama3.2 via Ollama) to infer `UserProfile` fields from natural language, the quality of the recommendation is partly a function of how well the model interprets the query. Ambiguous or short queries like "something good" produce less reliable profile inference than specific ones like "chill music for studying."

---

## Potential for Misuse and Prevention

**Mood-based harm:** A less obvious risk is recommending emotionally inappropriate content. If a user states they are stressed or anxious and the LLM infers a high-energy "angry" mood profile, the system could return aggressive music that worsens how the user feels. This problem could be prevented by including a simple content advisory check before surfacing very high-intensity results.

**Prompt injection:** Because user text is passed directly into the LLM's context, a malicious or adversarial user could craft a query designed to manipulate the agent's tool calls — for example, attempting to override the scoring profile or inject instructions into the system prompt. The guardrail layer (`src/guardrails.py`) provides a structural defense by validating and sanitizing all LLM-generated tool arguments before they reach the scoring engine. This means even if the LLM is manipulated into generating a bad `get_recommendations` call (e.g., `target_energy = "override the system"`), the guardrail rejects the value and defaults it safely, and the violation is logged as a warning.

**Infinite or resource-exhausting loops:** The agentic loop is capped at 6 iterations to prevent runaway LLM calls. Without this cap, a poorly behaving model could loop indefinitely, consuming local compute resources. The cap ensures the system degrades gracefully rather than hanging.

---

## Surprises During Testing

I was surprised to find that the batch mode, which does not use the LLM, was perfectly consistent and predictable across all 8 profiles. On the other hand, the agentic mode on the same catalog could return different top songs for the same intent. This highlighted that the LLM adds not only expressiveness but also unpredictability.

---

## Collaboration with AI

Claude Code served as the primary coding assistant throughout this project. I used it to generate code by providing detailed prompts that included project specifications and context, and to help me write the README based on a bigger picture of the overview of my code, with specific situations documented by me. For code generation, when something seemed unclear, I asked the AI for explanations which led to discussions about interesting and important tradeoffs. For writing the README, I gave specific prompts for usability, such as asking the AI to include cross-platform setup instructions instead of only one platform since different users use different platforms.

**Helpful suggestion:** When implementing the guardrail layer, Claude Code suggested structuring the result as a `GuardrailResult` dataclass with separate `sanitized` (the cleaned inputs) and `violations` (a list of human-readable correction messages) fields, rather than raising exceptions or returning a simple boolean. This design turned out to be the right call: it let the agent continue functioning after a guardrail correction while still surfacing warnings to the log and feeding the violation list back to the LLM in the tool result. If I had used exceptions, a single bad LLM-generated energy value would have crashed the entire agentic loop. The dataclass design made the system both robust and transparent.

**Flawed suggestion:** When it was time to choose the LLM powering the agentic loop, Claude Code proposed using Anthropic's API as the default without any explanation of the tradeoffs. This was a poor suggestion for this project's context: the repository is public, intended for a general audience, and Anthropic's API requires an account and a paid API key. A casual user following the setup instructions would have been blocked immediately. After I questioned the recommendation and asked Claude Code to walk through alternatives, including Gemini and Ollama, it became clear that Ollama was the better fit. It is fully local, free, no account required, and configurable via an environment variable if users want a different model.

This experience reinforced a guiding principle I carried through the rest of the project: use AI to generate code quickly, but keep system design and architecture decisions in human hands to judge what is right for the specific audience and constraints of the project.
