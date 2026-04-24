from datetime import date
from pathlib import Path

from core.algo.consolidate import write_playbook
from core.algo.export import (
    ExportContext,
    SENTINEL_BEGIN,
    SENTINEL_END,
    merge_into,
    render_agents_md,
)
from core.schema import MemoryEntry, Playbook


def _bootstrap(memory_dir: Path, entries: list[MemoryEntry]) -> None:
    pb = Playbook(root=memory_dir)
    pb.entries = entries
    write_playbook(memory_dir, pb)


def test_render_includes_active_entries(tmp_path: Path):
    memory = tmp_path / "memory" / "demo"
    _bootstrap(memory, [
        MemoryEntry(id="pref-00001", topic="preferences", text="use tabs", created=date(2026, 1, 1)),
        MemoryEntry(id="corr-00001", topic="corrections",
                    text="never mock the database", created=date(2026, 1, 1)),
    ])
    ctx = ExportContext(hypha_root=tmp_path, project="demo")
    out = render_agents_md(ctx)

    assert SENTINEL_BEGIN in out
    assert SENTINEL_END in out
    assert "use tabs" in out
    assert "never mock the database" in out
    assert "Common corrections" in out


def test_render_excludes_superseded(tmp_path: Path):
    memory = tmp_path / "memory" / "demo"
    _bootstrap(memory, [
        MemoryEntry(id="pref-00001", topic="preferences",
                    text="old rule", created=date(2026, 1, 1),
                    superseded_by="pref-00002"),
        MemoryEntry(id="pref-00002", topic="preferences",
                    text="new rule", created=date(2026, 1, 1)),
    ])
    ctx = ExportContext(hypha_root=tmp_path, project="demo")
    out = render_agents_md(ctx)

    assert "new rule" in out
    assert "old rule" not in out


def test_per_topic_limit_applies(tmp_path: Path):
    memory = tmp_path / "memory" / "demo"
    entries = [
        MemoryEntry(id=f"pref-{i:05d}", topic="preferences",
                    text=f"rule {i}", created=date(2026, 1, 1))
        for i in range(1, 11)
    ]
    _bootstrap(memory, entries)
    ctx = ExportContext(hypha_root=tmp_path, project="demo", per_topic_limit=3)
    out = render_agents_md(ctx)

    assert "rule 1" in out
    assert "rule 3" in out
    assert "rule 4" not in out
    assert "+7 more" in out


def test_merge_creates_file_when_missing(tmp_path: Path):
    agents = tmp_path / "AGENTS.md"
    assert not agents.exists()
    block = f"{SENTINEL_BEGIN}\nhello\n{SENTINEL_END}\n"
    merged = merge_into(agents, block)
    assert "# AGENTS.md" in merged
    assert block in merged


def test_merge_is_idempotent(tmp_path: Path):
    agents = tmp_path / "AGENTS.md"
    agents.write_text("# AGENTS.md\n\n## My rules\n- be nice\n\n", encoding="utf-8")
    block1 = f"{SENTINEL_BEGIN}\nfirst block\n{SENTINEL_END}\n"
    merged1 = merge_into(agents, block1)
    assert "first block" in merged1
    assert "be nice" in merged1

    # Write it to disk and merge a replacement block.
    agents.write_text(merged1, encoding="utf-8")
    block2 = f"{SENTINEL_BEGIN}\nsecond block\n{SENTINEL_END}\n"
    merged2 = merge_into(agents, block2)

    # The user's "be nice" rule must survive.
    assert "be nice" in merged2
    # Only one block pair must exist.
    assert merged2.count(SENTINEL_BEGIN) == 1
    assert merged2.count(SENTINEL_END) == 1
    # And it must be the new content.
    assert "second block" in merged2
    assert "first block" not in merged2
