"""Critical regression guard: consolidate apply must NEVER silently drop old entries.

This was v0.1's #1 data-loss bug — _load_playbook returned an empty Playbook,
so every consolidate run overwrote topic files with only the newly added ones.
"""
from datetime import date
from pathlib import Path

from core.algo.consolidate import ConsolidateContext, apply, write_playbook
from core.schema import MemoryEntry, Playbook


def _bootstrap_playbook(memory_dir: Path, n: int = 5) -> None:
    memory_dir.mkdir(parents=True, exist_ok=True)
    pb = Playbook(root=memory_dir)
    for i in range(1, n + 1):
        pb.entries.append(MemoryEntry(
            id=f"corr-{i:05d}",
            topic="corrections",
            text=f"lesson {i}",
            created=date(2026, 4, 1),
            source=f"session-{i}",
        ))
    write_playbook(memory_dir, pb)


def test_apply_preserves_old_entries(tmp_path: Path):
    memory = tmp_path / "memory" / "demo"
    _bootstrap_playbook(memory, n=5)

    ctx = ConsolidateContext(hypha_root=tmp_path, project="demo")
    stats = apply(ctx, {"operations": [{
        "type": "ADD",
        "topic": "preferences",
        "text": "new pref",
        "date": "2026-04-24",
        "source": "session-new",
    }]})

    assert stats["added"] == 1
    pb = Playbook.load(memory)
    # Old corrections must still be there.
    assert sum(1 for e in pb.entries if e.topic == "corrections") == 5
    assert sum(1 for e in pb.entries if e.topic == "preferences") == 1


def test_apply_supersede_marks_without_deletion(tmp_path: Path):
    memory = tmp_path / "memory" / "demo"
    _bootstrap_playbook(memory, n=3)

    ctx = ConsolidateContext(hypha_root=tmp_path, project="demo")
    apply(ctx, {"operations": [{
        "type": "SUPERSEDE",
        "target_id": "corr-00001",
        "new_id": "corr-00010",
    }]})

    pb = Playbook.load(memory)
    superseded = [e for e in pb.entries if e.id == "corr-00001"][0]
    assert superseded.superseded_by == "corr-00010"
    # The old entry is still loadable — nothing was physically deleted.
    assert superseded.text == "lesson 1"


def test_dry_run_makes_no_changes(tmp_path: Path):
    memory = tmp_path / "memory" / "demo"
    _bootstrap_playbook(memory, n=3)
    before = (memory / "corrections.md").read_text(encoding="utf-8")

    ctx = ConsolidateContext(hypha_root=tmp_path, project="demo", dry_run=True)
    stats = apply(ctx, {"operations": [{"type": "ADD", "topic": "preferences",
                                         "text": "x", "date": "2026-04-24"}]})
    assert stats["dry_run"] is True

    after = (memory / "corrections.md").read_text(encoding="utf-8")
    assert before == after
    assert not (memory / "preferences.md").exists()
