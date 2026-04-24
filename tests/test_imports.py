from pathlib import Path

from core.algo.imports import ImportContext, parse_frontmatter, run
from core.schema import Playbook


def _write_bible(dir_: Path, name: str, typ: str, desc: str, body: str = "body") -> Path:
    p = dir_ / f"{name}.md"
    p.write_text(
        f"---\nname: {name}\ndescription: {desc}\ntype: {typ}\n---\n{body}\n",
        encoding="utf-8",
    )
    return p


def test_parse_frontmatter_basic():
    fm, body = parse_frontmatter("---\nname: foo\ndescription: bar\n---\nhello\n")
    assert fm == {"name": "foo", "description": "bar"}
    assert body.strip() == "hello"


def test_parse_frontmatter_no_fm():
    fm, body = parse_frontmatter("no frontmatter here\njust text\n")
    assert fm == {}
    assert body.startswith("no frontmatter")


def test_import_maps_type_to_topic(tmp_path: Path):
    src = tmp_path / "src"
    src.mkdir()
    _write_bible(src, "a", "feedback", "one")
    _write_bible(src, "b", "project", "two")
    _write_bible(src, "c", "reference", "three")
    _write_bible(src, "d", "user", "four")
    _write_bible(src, "e", "unknown-type", "five")

    ctx = ImportContext(hypha_root=tmp_path / "hypha", project="demo", source_dir=src)
    stats = run(ctx)
    assert stats["added"] == 5

    pb = Playbook.load(tmp_path / "hypha" / "memory" / "demo")
    by_topic = {}
    for e in pb.entries:
        by_topic.setdefault(e.topic, []).append(e)
    assert len(by_topic["corrections"]) == 1
    assert len(by_topic["decisions"]) == 1
    assert len(by_topic["facts"]) == 2  # reference + unknown-type
    assert len(by_topic["preferences"]) == 1


def test_import_is_idempotent(tmp_path: Path):
    src = tmp_path / "src"
    src.mkdir()
    _write_bible(src, "a", "feedback", "desc1")

    ctx = ImportContext(hypha_root=tmp_path / "hypha", project="demo", source_dir=src)
    run(ctx)  # first
    s2 = run(ctx)  # second
    assert s2["added"] == 0
    assert s2["unchanged"] == 1
    assert s2["updated"] == 0


def test_import_detects_updated_description(tmp_path: Path):
    src = tmp_path / "src"
    src.mkdir()
    f = _write_bible(src, "a", "feedback", "original desc")

    ctx = ImportContext(hypha_root=tmp_path / "hypha", project="demo", source_dir=src)
    run(ctx)

    f.write_text(
        "---\nname: a\ndescription: updated desc\ntype: feedback\n---\nbody\n",
        encoding="utf-8",
    )
    s = run(ctx)
    assert s["updated"] == 1
    assert s["added"] == 0
    assert s["unchanged"] == 0

    pb = Playbook.load(tmp_path / "hypha" / "memory" / "demo")
    assert pb.entries[0].text == "updated desc"


def test_skipped_when_no_frontmatter(tmp_path: Path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "plain.md").write_text("just prose, no frontmatter\n", encoding="utf-8")

    ctx = ImportContext(hypha_root=tmp_path / "hypha", project="demo", source_dir=src)
    stats = run(ctx)
    assert stats["skipped_no_frontmatter"] == 1
    assert stats["added"] == 0
