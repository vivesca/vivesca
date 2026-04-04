from __future__ import annotations

import tempfile
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from metabolon.organelles.sporulation import (
    _now_iso,
    _parse_frontmatter,
    _scan_content,
    _to_slug,
    catalog,
    checkpoint_post,
    dormant_posts,
    germinate_post,
    list_checkpoints,
    mutate_post,
    propagate_site,
    publish,
)


def test_now_iso():
    result = _now_iso()
    assert len(result) == 24  # YYYY-MM-DDTHH:MM:SS.000Z
    assert result.endswith(".000Z")


@pytest.mark.parametrize(
    "input_title, expected_slug",
    [
        ("Hello World!", "hello-world"),
        ("  Multiple   Spaces  ", "multiple-spaces"),
        ("Some!@#$%^&*()Special", "somespecial"),
        ("Title-with-dashes", "title-with-dashes"),
        ("title_with_underscores", "title-with-underscores"),
        ("123 Numbers", "123-numbers"),
    ],
)
def test_to_slug(input_title, expected_slug):
    assert _to_slug(input_title) == expected_slug


def test_organelles_sporulation_parse_frontmatter_valid():
    content = """---
title: "Test Post"
pubDatetime: 2024-01-01T00:00:00.000Z
draft: true
tags: [test, example]
---

# Body
"""
    result = _parse_frontmatter(content)
    assert result is not None
    assert result["title"] == "Test Post"
    assert result["pubDatetime"] == "2024-01-01T00:00:00.000Z"
    assert result["draft"] is True
    assert result["tags"] == ["test", "example"]
    assert "_body_offset" in result


def test_parse_frontmatter_no_closing():
    content = """---
title: "Test"
"""
    result = _parse_frontmatter(content)
    assert result is None


def test_parse_frontmatter_not_started():
    content = """title: "Test"
---
"""
    result = _parse_frontmatter(content)
    assert result is None


@pytest.mark.parametrize(
    "content, expected_warnings",
    [
        ("My password: abc123456789", 1),
        ("api_key = ABCDEFGHIJKLMN", 1),
        ("HKD 1000", 1),
        ("5 million dollars", 1),
        ("Mr. Smith", 1),
        ("No sensitive content here", 0),
        ("secret: 12345678", 1),
    ],
)
def test_scan_content(content, expected_warnings):
    warnings = _scan_content(content)
    assert len(warnings) == expected_warnings


def test_scan_content_snippet_in_warning():
    warnings = _scan_content("My secret: mypassword12345 something else")
    assert len(warnings) == 1
    assert "possible credential" in warnings[0]
    assert "mypassword12345" in warnings[0]


@patch("metabolon.organelles.sporulation.PUBLISHED_DIR")
def test_organelles_sporulation_germinate_post_creates_file(mock_published_dir):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        mock_published_dir.mkdir = MagicMock()
        mock_published_dir.__bool__ = MagicMock(return_value=True)
        mock_published_dir.__str__ = MagicMock(return_value=str(tmp_path))
        mock_published_dir.__truediv__ = lambda self, name: tmp_path / name

        with patch("metabolon.organelles.sporulation.PUBLISHED_DIR", tmp_path):
            result = germinate_post("Test New Post")
            assert result["created"] is True
            assert (tmp_path / "test-new-post.md").exists()
            content = (tmp_path / "test-new-post.md").read_text()
            assert 'title: "Test New Post"' in content
            assert "draft: true" in content


@patch("metabolon.organelles.sporulation.PUBLISHED_DIR")
def test_germinate_post_already_exists(mock_published_dir):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        existing = tmp_path / "existing-post.md"
        existing.write_text("---\ntitle: Existing\n---\n")

        with patch("metabolon.organelles.sporulation.PUBLISHED_DIR", tmp_path):
            result = germinate_post("Existing Post")
            assert "error" in result
            assert "already exists" in result["error"]


@patch("metabolon.organelles.sporulation.PUBLISHED_DIR")
def test_dormant_posts_empty(mock_published_dir):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        with patch("metabolon.organelles.sporulation.PUBLISHED_DIR", tmp_path):
            result = dormant_posts()
            assert result == []


@patch("metabolon.organelles.sporulation.PUBLISHED_DIR")
def test_dormant_posts_list(mock_published_dir):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        post1 = tmp_path / "post-one.md"
        post1.write_text("""---
title: "Post One"
pubDatetime: 2024-02-01T00:00:00.000Z
draft: false
---
Body content here with some words.
""")
        post2 = tmp_path / "post-two.md"
        post2.write_text("""---
title: "Post Two"
pubDatetime: 2024-03-01T00:00:00.000Z
draft: true
---
Another body with more words.
""")

        with patch("metabolon.organelles.sporulation.PUBLISHED_DIR", tmp_path):
            result = dormant_posts()
            assert len(result) == 2
            # Should be sorted newest first
            assert result[0]["slug"] == "post-two"
            assert result[1]["slug"] == "post-one"
            assert result[0]["draft"] is True
            assert result[1]["draft"] is False
            assert result[0]["words"] == 5
            assert result[1]["words"] == 6


@patch("metabolon.organelles.sporulation.PUBLISHED_DIR")
def test_publish_not_found(mock_published_dir):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        with patch("metabolon.organelles.sporulation.PUBLISHED_DIR", tmp_path):
            result = publish("nonexistent")
            assert "error" in result
            assert "No post found" in result["error"]


@patch("metabolon.organelles.sporulation.PUBLISHED_DIR")
def test_organelles_sporulation_publish_already_published(mock_published_dir):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        post = tmp_path / "published.md"
        post.write_text("""---
title: Published
pubDatetime: 2024-01-01T00:00:00Z
draft: false
---
Body
""")
        with patch("metabolon.organelles.sporulation.PUBLISHED_DIR", tmp_path):
            result = publish("published")
            assert result["already_published"] is True


@patch("metabolon.organelles.sporulation.PUBLISHED_DIR")
def test_publish_success(mock_published_dir):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        post = tmp_path / "draft-post.md"
        post.write_text("""---
title: "Draft Post"
pubDatetime: 2024-01-01T00:00:00.000Z
draft: true
---
Body content.
""")
        with patch("metabolon.organelles.sporulation.PUBLISHED_DIR", tmp_path):
            result = publish("draft-post")
            assert result["published"] is True
            assert result["title"] == "Draft Post"
            content = post.read_text()
            assert "draft: false" in content
            assert "draft: true" not in content


@patch("metabolon.organelles.sporulation.propagate_site")
@patch("metabolon.organelles.sporulation.PUBLISHED_DIR")
def test_organelles_sporulation_publish_with_push(mock_published_dir, mock_propagate):
    mock_propagate.return_value = {"pushed": True, "url": "https://example.com"}
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        post = tmp_path / "draft-post.md"
        post.write_text("""---
title: "Draft Post"
pubDatetime: 2024-01-01T00:00:00.000Z
draft: true
---
Body content.
""")
        with patch("metabolon.organelles.sporulation.PUBLISHED_DIR", tmp_path):
            result = publish("draft-post", push=True)
            assert result["published"] is True
            assert "push" in result
            mock_propagate.assert_called_once()


@patch("metabolon.organelles.sporulation.PUBLISHED_DIR")
def test_mutate_post_not_found(mock_published_dir):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        with patch("metabolon.organelles.sporulation.PUBLISHED_DIR", tmp_path):
            result = mutate_post("nonexistent", "test note")
            assert "error" in result


@patch("metabolon.organelles.sporulation.PUBLISHED_DIR")
def test_mutate_post_adds_note_and_modtime(mock_published_dir):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        post = tmp_path / "test-post.md"
        post.write_text("""---
title: "Test Post"
pubDatetime: 2024-01-01T00:00:00.000Z
draft: false
---
Body
""")
        with patch("metabolon.organelles.sporulation.PUBLISHED_DIR", tmp_path):
            datetime.now(UTC)
            result = mutate_post("test-post", "Fixed typo")
            datetime.now(UTC)
            assert result["revised"] is True
            content = post.read_text()
            assert 'revisionNote: "Fixed typo"' in content
            assert "modDatetime: " in content


@patch("metabolon.organelles.sporulation.SYNC_SCRIPT")
def test_propagate_site_not_found(mock_sync_script):
    mock_sync_script.exists.return_value = False
    mock_sync_script.__str__ = MagicMock(return_value="/fake/path/sync.sh")
    with patch("metabolon.organelles.sporulation.SYNC_SCRIPT", mock_sync_script):
        result = propagate_site()
        assert "error" in result
        assert "Sync script not found" in result["error"]


@patch("metabolon.organelles.sporulation.subprocess.run")
@patch("metabolon.organelles.sporulation.SYNC_SCRIPT")
def test_organelles_sporulation_propagate_site_success(mock_sync_script, mock_subprocess_run):
    mock_sync_script.exists.return_value = True
    mock_sync_script.__str__ = MagicMock(return_value="/fake/path/sync.sh")

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stderr = ""
    mock_subprocess_run.return_value = mock_result

    with patch("metabolon.organelles.sporulation.SYNC_SCRIPT", mock_sync_script):
        result = propagate_site()
        assert result["pushed"] is True
        assert result["url"] == "https://terryli.hm"
        mock_subprocess_run.assert_called_once()


@patch("metabolon.organelles.sporulation.subprocess.run")
@patch("metabolon.organelles.sporulation.SYNC_SCRIPT")
def test_organelles_sporulation_propagate_site_failure(mock_sync_script, mock_subprocess_run):
    mock_sync_script.exists.return_value = True
    mock_sync_script.__str__ = MagicMock(return_value="/fake/path/sync.sh")

    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "Something went wrong"
    mock_subprocess_run.return_value = mock_result

    with patch("metabolon.organelles.sporulation.SYNC_SCRIPT", mock_sync_script):
        result = propagate_site()
        assert "error" in result
        assert "Sync failed" in result["error"]
        assert "Something went wrong" in result["error"]


@patch("metabolon.organelles.sporulation.PUBLISHED_DIR")
@patch("metabolon.organelles.sporulation.CHECKPOINT_DIR")
def test_checkpoint_post_not_found(mock_checkpoint_dir, mock_published_dir):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        mock_checkpoint_dir.mkdir = MagicMock()
        mock_checkpoint_dir.__truediv__ = lambda self, name: tmp_path / name
        with patch("metabolon.organelles.sporulation.PUBLISHED_DIR", tmp_path):
            result = checkpoint_post("nonexistent", "test checkpoint")
            assert "error" in result


@patch("metabolon.organelles.sporulation.PUBLISHED_DIR")
def test_checkpoint_post_creates_checkpoint(mock_published_dir):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        published_dir = tmp_path / "published"
        checkpoint_dir = tmp_path / "checkpoints"
        published_dir.mkdir()
        post = published_dir / "test-post.md"
        post.write_text("""---
title: Test
---
Body content
""")

        with (
            patch("metabolon.organelles.sporulation.PUBLISHED_DIR", published_dir),
            patch("metabolon.organelles.sporulation.CHECKPOINT_DIR", checkpoint_dir),
        ):
            result = checkpoint_post("test-post", "Before edit")
            assert result["checkpoint"] is True
            assert "codename" in result
            checkpoints = list(checkpoint_dir.glob("*.md"))
            assert len(checkpoints) == 1
            assert "Before edit" in checkpoints[0].read_text()


@patch("metabolon.organelles.sporulation.CHECKPOINT_DIR")
def test_list_checkpoints_empty(mock_checkpoint_dir):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        mock_checkpoint_dir.exists.return_value = False
        with patch("metabolon.organelles.sporulation.CHECKPOINT_DIR", tmp_path):
            result = list_checkpoints()
            assert result == []


@patch("metabolon.organelles.sporulation.INDEX_PATH")
@patch("metabolon.organelles.sporulation.PUBLISHED_DIR")
def test_organelles_sporulation_catalog_creates_index(mock_published_dir, mock_index_path):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        published_dir = tmp_path / "published"
        index_path = tmp_path / "terryli.hm.md"
        published_dir.mkdir()

        post1 = published_dir / "post-one.md"
        post1.write_text("""---
title: "Post One"
pubDatetime: 2024-02-01T00:00:00.000Z
description: "First post"
draft: false
tags: [test, personal]
---
Body
""")

        post2 = published_dir / "post-two.md"
        post2.write_text("""---
title: "Post Two"
pubDatetime: 2024-03-01T00:00:00.000Z
description: "Second post"
draft: false
tags: [tech]
---
Body
""")

        with (
            patch("metabolon.organelles.sporulation.PUBLISHED_DIR", published_dir),
            patch("metabolon.organelles.sporulation.INDEX_PATH", index_path),
        ):
            result = catalog()
            assert result["indexed"] == 2
            assert index_path.exists()
            content = index_path.read_text()
            assert "2 posts" in content
            assert "Post One" in content
            assert "Post Two" in content
            assert "### test" in content
            assert "### tech" in content


@patch("metabolon.organelles.sporulation.INDEX_PATH")
@patch("metabolon.organelles.sporulation.PUBLISHED_DIR")
def test_organelles_sporulation_catalog_skips_drafts(mock_published_dir, mock_index_path):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        published_dir = tmp_path / "published"
        index_path = tmp_path / "terryli.hm.md"
        published_dir.mkdir()

        post = published_dir / "draft-post.md"
        post.write_text("""---
title: "Draft"
pubDatetime: 2024-01-01T00:00:00Z
description: "Unpublished"
draft: true
---
Body
""")

        with (
            patch("metabolon.organelles.sporulation.PUBLISHED_DIR", published_dir),
            patch("metabolon.organelles.sporulation.INDEX_PATH", index_path),
        ):
            result = catalog()
            assert result["indexed"] == 0
