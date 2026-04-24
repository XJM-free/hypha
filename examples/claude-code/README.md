# Example: Claude Code + Hypha

A walkthrough of wiring Hypha into a fresh Claude Code setup.

## 1. Install

```bash
git clone https://github.com/XJM-free/hypha && cd hypha
pip install -e .
hypha init
```

## 2. Copy hooks

```bash
mkdir -p ~/.claude/hypha-hooks
cp adapters/claude-code/hooks/*.sh ~/.claude/hypha-hooks/
chmod +x ~/.claude/hypha-hooks/*.sh
```

## 3. Merge settings

Open `~/.claude/settings.json` and merge the `hooks` block from
[`adapters/claude-code/settings.example.json`](../../adapters/claude-code/settings.example.json).
Do **not** replace the file — you almost certainly have other hooks already.

## 4. Verify

Open Claude Code in any project and run:

```
/status
```

You should see the five Hypha hooks registered. Check logs at
`~/.hypha/logs/` after a few sessions.

## 5. First consolidation

After 5+ sessions across 24+ hours, `memory_consolidate.sh` fires
automatically. To trigger manually:

```bash
hypha consolidate --llm "claude -p --bare --setting-sources '' --output-format json"
```

Inspect the result:

```bash
ls ~/.hypha/memory/<project>/
cat ~/.hypha/memory/<project>/MEMORY.md
```
