"""Tests for chromatin organelle — file-based memory store."""

from metabolon.organelles.chromatin import _parse_frontmatter, _MarkIndex


# --- _parse_frontmatter ---

def test_parse_frontmatter_basic():
    text = "---\nname: test\ntype: feedback\n---\nBody text"
    meta = _parse_frontmatter(text)
    assert meta["name"] == "test"
    assert meta["type"] == "feedback"


def test_parse_frontmatter_empty():
    assert _parse_frontmatter("No frontmatter here") == {}


def test_parse_frontmatter_empty_value():
    text = "---\nname:\ntype: user\n---\n"
    meta = _parse_frontmatter(text)
    assert meta["name"] == ""
    assert meta["type"] == "user"


def test_parse_frontmatter_colons_in_value():
    text = "---\ndescription: key: value pair\n---\n"
    meta = _parse_frontmatter(text)
    assert meta["description"] == "key: value pair"


# --- _MarkIndex ---

def test_index_empty_dir(tmp_path):
    idx = _MarkIndex(tmp_path)
    idx.ensure_loaded()
    assert idx.query(".*") == []


def test_index_loads_files(tmp_path):
    (tmp_path / "test.md").write_text("---\nname: test\ntype: feedback\n---\nSome content here")
    idx = _MarkIndex(tmp_path)
    idx.ensure_loaded()
    results = idx.query("content")
    assert len(results) == 1
    assert results[0]["name"] == "test"


def test_index_filter_by_category(tmp_path):
    (tmp_path / "a.md").write_text("---\nname: a\ncategory: important\n---\nAAA")
    (tmp_path / "b.md").write_text("---\nname: b\ncategory: trivial\n---\nBBB")
    idx = _MarkIndex(tmp_path)
    results = idx.query(".*", category="important")
    assert len(results) == 1
    assert results[0]["name"] == "a"


def test_index_filter_nonexistent_category(tmp_path):
    (tmp_path / "a.md").write_text("---\nname: a\ncategory: x\n---\ntext")
    idx = _MarkIndex(tmp_path)
    results = idx.query(".*", category="nonexistent")
    assert results == []


def test_index_filter_by_source(tmp_path):
    (tmp_path / "a.md").write_text("---\nname: a\nsource: cc\n---\ntext")
    (tmp_path / "b.md").write_text("---\nname: b\nsource: goose\n---\ntext")
    idx = _MarkIndex(tmp_path)
    results = idx.query("text", source_enzyme="cc")
    assert len(results) == 1
    assert results[0]["name"] == "a"


def test_index_regex_filter(tmp_path):
    (tmp_path / "a.md").write_text("---\nname: a\n---\napple banana")
    (tmp_path / "b.md").write_text("---\nname: b\n---\ncherry date")
    idx = _MarkIndex(tmp_path)
    results = idx.query("apple")
    assert len(results) == 1


def test_index_limit(tmp_path):
    for i in range(5):
        (tmp_path / f"m{i}.md").write_text(f"---\nname: m{i}\n---\ncommon word")
    idx = _MarkIndex(tmp_path)
    results = idx.query("common", limit=2)
    assert len(results) == 2


def test_index_reload(tmp_path):
    (tmp_path / "a.md").write_text("---\nname: a\n---\noriginal")
    idx = _MarkIndex(tmp_path)
    idx.ensure_loaded()
    assert len(idx.query("original")) == 1
    # Modify file
    (tmp_path / "a.md").write_text("---\nname: a\n---\nmodified")
    idx.reload()
    idx.ensure_loaded()
    assert len(idx.query("modified")) == 1
    assert len(idx.query("original")) == 0


def test_index_invalidate(tmp_path):
    (tmp_path / "a.md").write_text("---\nname: a\ncategory: old\n---\ntext")
    idx = _MarkIndex(tmp_path)
    idx.ensure_loaded()
    assert len(idx.query("text", category="old")) == 1
    # Update file and invalidate
    (tmp_path / "a.md").write_text("---\nname: a\ncategory: new\n---\ntext")
    idx.invalidate("a.md")
    assert len(idx.query("text", category="new")) == 1
    assert len(idx.query("text", category="old")) == 0


def test_index_missing_dir(tmp_path):
    missing = tmp_path / "nonexistent"
    idx = _MarkIndex(missing)
    idx.ensure_loaded()
    assert idx.query(".*") == []
    assert missing.exists()  # should create it
