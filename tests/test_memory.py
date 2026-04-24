from datetime import date
from pathlib import Path

from core.algo.consolidate import write_playbook
from core.schema import MemoryEntry, Playbook


def _entry(**kw) -> MemoryEntry:
    defaults = dict(
        id="pref-00001",
        topic="preferences",
        text="always use tabs",
        created=date(2026, 4, 24),
        source="session-abc",
    )
    defaults.update(kw)
    return MemoryEntry(**defaults)


def test_render_and_parse_roundtrip(tmp_path: Path):
    pb = Playbook(root=tmp_path)
    pb.entries = [
        _entry(id="pref-00001", text="alpha", helpful=3),
        _entry(id="pref-00002", topic="decisions", text="beta", source="session-x"),
        _entry(id="pref-00003", topic="corrections", text="gamma", superseded_by="pref-99999"),
    ]
    # decisions entries use `deci-` prefix in practice; parser tolerates any id.
    pb.entries[1].id = "deci-00001"
    pb.entries[2].id = "corr-00001"

    write_playbook(tmp_path, pb)
    loaded = Playbook.load(tmp_path)

    by_id = {e.id: e for e in loaded.entries}
    assert by_id["pref-00001"].text == "alpha"
    assert by_id["pref-00001"].helpful == 3
    assert by_id["deci-00001"].source == "session-x"
    assert by_id["corr-00001"].superseded_by == "pref-99999"


def test_next_id_skips_existing(tmp_path: Path):
    pb = Playbook(root=tmp_path)
    pb.entries.append(_entry(id="pref-00001"))
    pb.entries.append(_entry(id="pref-00003"))
    # Should pick the first unused integer, not len() + 1.
    assert pb.next_id("preferences") == "pref-00002"
    pb.entries.append(_entry(id="pref-00002"))
    assert pb.next_id("preferences") == "pref-00004"


def test_by_source_matches_exact_path(tmp_path: Path):
    pb = Playbook(root=tmp_path)
    pb.entries.append(_entry(source="/abs/path/a.md"))
    pb.entries.append(_entry(id="pref-00002", source="/abs/path/b.md"))
    assert pb.by_source("/abs/path/a.md").id == "pref-00001"
    assert pb.by_source("/abs/path/missing.md") is None


def test_load_ignores_unparseable_lines(tmp_path: Path):
    (tmp_path / "preferences.md").write_text(
        "# preferences\n"
        "\n"
        "this is a freeform paragraph the user added manually\n"
        "- [2026-04-24] real entry (id=pref-00001 helpful=0 harmful=0)\n"
        "- garbage not matching format\n",
        encoding="utf-8",
    )
    pb = Playbook.load(tmp_path)
    assert len(pb.entries) == 1
    assert pb.entries[0].text == "real entry"
