# AI layer

`AIProvider` defines `status()`, `generate_analysis(evidence)` and `generate_fix_validation(comparison)`.
`OllamaGemmaProvider` implements it against Ollama's local `/api/chat` with a JSON-schema `format`.

## Flow

1. `ai/service.py` builds bounded evidence: configuration, measured metrics, ≤ 20 timeline lines, limitations, a
   deterministic severity hint and optional developer-pasted code. Nothing else is sent; the model has no tool access.
2. The prompt requires evidence-only answers, hypotheses phrased as hypotheses, and stack-specific code.
3. The reply is validated with Pydantic (`AnalysisResult`). Invalid output is retried once, then `502 ai_invalid_output`.
4. Valid results are stored as `AIAnalysis` plus a `FixRecord` (status `proposed`).

## Errors (never replaced by fabricated output)

| Situation | Response |
|---|---|
| Ollama not running | 503 `ai_unavailable` with the `ollama serve` hint |
| Model not installed | 503 `ai_model_missing` with the `ollama pull` command |
| Timeout | 503 with a retry hint |
| Invalid output after retry | 502 `ai_invalid_output` |

## Response schema

`finding`, `severity` (critical/high/medium/low), `severity_rationale`, `evidence[]`, `likely_cause`,
`recommended_actions[]`, `code_example{language,snippet,assumptions}`, `verification_steps[]`, plus
`what_happened` and `user_impact`.

Before/after verdicts are always produced by `metrics/comparison.py`; Gemma may only describe them.
