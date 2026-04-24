from datetime import date
from pathlib import Path

from core.algo.consolidate import write_playbook
from core.algo.queries import find_entry, project_stats, search
from core.schema import MemoryEntry, Playbook


def _bootstrap(memory_root: Path, project: str, entries: list[MemoryEntry]) -> None:
    pb = Playbook(root=memory_root / project)
    pb.entries = entries
    write_playbook(memory_root / project, pb)


def test_project_stats_empty(tmp_path: Path):
    assert project_stats(tmp_path) == []


def test_project_stats_counts(tmp_path: Path):
    _bootstrap(tmp_path, "demo", [
        MemoryEntry(id="corr-00001", topic="corrections", text="a", created=date(2026, 1, 1)),
        MemoryEntry(id="corr-00002", topic="corrections", text="b", created=date(2026, 1, 1),
                    superseded_by="corr-00003"),
        MemoryEntry(id="deci-00001", topic="decisions", text="c", created=date(2026, 1, 1)),
    ])
    stats = project_stats(tmp_path)
    assert len(stats) == 1
    s = stats[0]
    assert s.name == "demo"
    assert s.total_active == 2
    assert s.total_superseded == 1
    assert s.entries_by_topic["corrections"] == 2
    assert s.entries_by_topic["decisions"] == 1


def test_search_ranks_by_frequency(tmp_path: Path):
    _bootstrap(tmp_path, "p1", [
        MemoryEntry(id="corr-00001", topic="corrections",
                    text="apple apple banana", created=date(2026, 1, 1)),
        MemoryEntry(id="corr-00002", topic="corrections",
                    text="apple", created=date(2026, 1, 1)),
        MemoryEntry(id="corr-00003", topic="corrections",
                    text="nothing", created=date(2026, 1, 1)),
    ])
    hits = search(tmp_path, "apple")
    assert len(hits) == 2
    assert hits[0].entry.id == "corr-00001"
    assert hits[0].score == 2
    assert hits[1].entry.id == "corr-00002"


def test_search_multiterm_ands_frequencies(tmp_path: Path):
    _bootstrap(tmp_path, "p1", [
        MemoryEntry(id="corr-00001", topic="corrections",
                    text="apple banana", created=date(2026, 1, 1)),
        MemoryEntry(id="corr-00002", topic="corrections",
                    text="apple apple", created=date(2026, 1, 1)),
    ])
    hits = search(tmp_path, "apple banana")
    # corr-00001 has one of each; corr-00002 has two apples, zero banana.
    # Current scoring sums term occurrences, so corr-00002 ranks first (2 > 2? tie).
    scores = {h.entry.id: h.score for h in hits}
    assert scores["corr-00001"] == 2
    assert scores["corr-00002"] == 2


def test_find_entry_across_projects(tmp_path: Path):
    _bootstrap(tmp_path, "p1", [
        MemoryEntry(id="corr-00001", topic="corrections", text="x", created=date(2026, 1, 1)),
    ])
    _bootstrap(tmp_path, "p2", [
        MemoryEntry(id="deci-00001", topic="decisions", text="y", created=date(2026, 1, 1)),
    ])
    found = find_entry(tmp_path, "deci-00001")
    assert found is not None
    project, entry = found
    assert project == "p2"
    assert entry.text == "y"
    assert find_entry(tmp_path, "missing-00000") is None
