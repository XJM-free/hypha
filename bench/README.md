# Hypha Benchmarks

Two kinds of benchmarks live here:

## `tiny.jsonl` — smoke tests for `hypha guard`

Small, fast, project-specific. One JSON object per line:

```json
{"prompt": "...", "expected_substring": "..."}
```

Each case runs through your configured LLM (`--llm`), the output is checked
for `expected_substring`, and `guard` aggregates a score. The score is
compared against `baseline_score` (a single-line file containing the score as
a float); any regression beyond `noise_leeway` (default 0.1) causes
`hypha guard` to exit with code 2.

The example [`tiny.jsonl`](tiny.jsonl) contains five generic coding prompts to
demonstrate the format. **Replace with cases that matter for your workflow.**

Typical replacements:

- 3 cases testing a frequently-needed skill (e.g. "ask me to refactor a
  function — expect the word `extract`")
- 2 cases testing behavior regressions you've seen before
- 1 case testing a format convention (commit message style, lint rule, etc.)

Keep the total under 10 cases and under 30 seconds wall-clock so `guard` can
run as a synchronous PostToolUse hook without blocking Claude Code.

## `swe-skills-bench/` — reference integration for the 2026 research bench

[SWE-Skills-Bench (arXiv:2603.15401)](https://arxiv.org/abs/2603.15401) is the
first benchmark designed specifically to test whether agent "skills" are
useful — it uses paired skill conditions (with-skill vs without-skill) and
deterministic verification. That makes it a natural upstream signal for our
`hypha harvest` workflow.

We don't vendor it. See [`swe-skills-bench/README.md`](swe-skills-bench/README.md)
for how to wire it up as a quarterly evaluation gate for your skill library.
