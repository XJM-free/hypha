# SWE-Skills-Bench integration (reference)

[SWE-Skills-Bench](https://arxiv.org/abs/2603.15401) (March 2026) is the first
benchmark designed to directly measure whether agent skills help. It is the
ideal upstream signal for deciding whether a skill you harvested is pulling
its weight.

We don't vendor the bench (licensing, size). This README describes how to run
it against your Hypha-managed skill library as a quarterly evaluation.

## How it works

For each task, the bench provides:

- A task description
- A paired "with skill" / "without skill" condition
- Deterministic verification (test runs, exact-match, etc.)

If the with-skill condition doesn't beat the without-skill condition by more
than noise, the skill is not earning its keep.

## Suggested cadence

1. After harvesting 10-20 skills (typically 1-2 months), run a pass.
2. For skills that regress or don't improve: move them to `~/.hypha/skills/.rejected/`.
3. For skills that help: update their `helpful` counter.

## Pseudocode

```bash
for skill_dir in ~/.hypha/skills/*/; do
  skill_name=$(basename "$skill_dir")

  # 1. Isolate this skill: temporarily move all others out
  setup_eval_env "$skill_name"

  # 2. Run the bench's paired conditions
  with_score=$(swe-skills-bench --condition with --skills-dir ~/.hypha/skills)
  without_score=$(swe-skills-bench --condition without --skills-dir /dev/null)

  delta=$(echo "$with_score - $without_score" | bc -l)

  # 3. Update Hypha's counters via `hypha inbox` equivalents
  if (( $(echo "$delta < -0.05" | bc -l) )); then
    hypha inbox reject "$skill_name"
  fi
done
```

An official `hypha bench swe-skills` wrapper is planned for v0.2. Contributions
welcome — see [CONTRIBUTING.md](../../CONTRIBUTING.md).
