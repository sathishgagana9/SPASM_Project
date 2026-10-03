# Providers

**As of this update, Groq is the only supported provider — Ollama
support was removed entirely** (per project decision; it's not a
fallback, not commented-out, not dead code left in place — the
Ollama implementation file was deleted).

`GroqProvider` (`backend/app/providers/groq.py`) implements the
`LLMProvider` interface (`base.py`) against Groq's OpenAI-compatible
`/chat/completions` endpoint at `https://api.groq.com/openai/v1`.
Configure via `GROQ_API_KEY` in `backend/.env`. Constructing
`GroqProvider` with no key raises a `ProviderError` (`kind="auth"`)
immediately, rather than failing confusingly on the first request.

`app/providers/registry.py::get_provider(name)` only recognizes
`"groq"` — any other name raises a clear `ProviderError` explaining
Ollama was removed. The rest of the app depends only on the
`LLMProvider` interface, never `GroqProvider` directly, so adding a
second provider back later means one new branch in the registry, not
changes scattered through the codebase.

`GroqProvider` surfaces real errors (`ProviderError`, with a `kind`
of `timeout`/`unreachable`/`auth`/`rate_limit`/`malformed`) rather
than swallowing them — the chat API turns these into the appropriate
HTTP status with the underlying message, and the frontend
(`ErrorNotice.tsx`) maps each kind to distinct, honest copy.

## Why Groq

No local model/GPU needed, fast inference, free tier available.
Tradeoff: requires an API key and network access (no offline use),
and Groq periodically deprecates model names — check
[console.groq.com/docs/models](https://console.groq.com/docs/models)
before assuming a model name in this repo is still live.
