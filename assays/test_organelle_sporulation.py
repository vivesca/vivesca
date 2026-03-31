"""Tests for sporulation organelle module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from pathlib import Path
import tempfile
import pytest

from metabolon.organelles import sporulation


def test_sporulation_module_imports():
    """Test that sporulation module can be imported."""
    assert sporulation is not None


def test_to_slug_basic():
    """Test _to_slug converts titles to URL-friendly slugs."""
    cases = [
        ("Hello World", "hello-world"),
        ("Hello  World", "hello-world"),
        ("Test-File_Name", "test-file-name"),
        ("Title with!@#$%^&*()[]{}", "title-with"),
        ("  Leading and Trailing  ", "leading-and-trailing"),
        ("One Two Three", "one-two-three"),
    ]
    for input_title, expected in cases:
        result = sporulation._to_slug(input_title)
        assert result == expected


def test_parse_frontmatter_valid():
    """Test _parse_frontmatter correctly parses valid YAML frontmatter."""
    content = """---
title: "Test Post"
draft: true
tags: [blog, test, python]
pubDatetime: 2024-01-01T00:00:00Z
---
Body content here.
"""
    result = sporulation._parse_frontmatter(content)
    assert result is not None
    assert result["title"] == "Test Post"
    assert result["draft"] is True
    assert result["tags"] == ["blog", "test", "python"]
    assert result["pubDatetime"] == "2024-01-01T00:00:00Z"
    assert "_body_offset" in result


def test_parse_frontmatter_invalid_no_closing():
    """Test _parse_frontmatter returns None for incomplete frontmatter."""
    content = """---
title: "Test Post"
Body content here.
"""
    result = sporulation._parse_frontmatter(content)
    assert result is None


def test_parse_frontmatter_no_frontmatter():
    """Test _parse_frontmatter returns None when no frontmatter."""
    content = "Just plain text\nno frontmatter here."
    result = sporulation._parse_frontmatter(content)
    assert result is None


def test_scan_content_detects_sensitive_content():
    """Test _scan_content detects potential sensitive information."""
    # Test password detection
    content = "My password: abc123DEF456"
    warnings = sporulation._scan_content(content)
    assert len(warnings) > 0
    assert "possible credential" in warnings[0]

    # Test named individual
    content = "Meeting with Dr. Smith next week"
    warnings = sporulation._scan_content(content)
    assert len(warnings) > 0
    assert "named individual" in warnings[0]

    # Test dollar amount
    content = "The price is $100"
    warnings = sporulation._scan_content(content)
    assert len(warnings) > 0
    assert "exact dollar figure" in warnings[0]

    # No sensitive content
    content = "This is a harmless blog post about Python"
    warnings = sporulation._scan_content(content)
    assert len(warnings) == 0


def test_germinate_post_creates_file(tmp_path):
    """Test germinate_post creates a new post with correct frontmatter."""
    with patch.object(sporulation, 'PUBLISHED_DIR', tmp_path):
        result = sporulation.germinate_post("My New Post")
        assert result["created"] is True
        assert result["slug"] == "my-new-post"
        assert Path(result["path"]).exists()
        content = Path(result["path"]).read_text()
        assert "---" in content
        assert "title: \"My New Post\"" in content
        assert "draft: true" in content


def test_germinate_post_prevents_duplicates(tmp_path):
    """Test germinate_post errors when post slug already exists."""
    with patch.object(sporulation, 'PUBLISHED_DIR', tmp_path):
        # Create first post
        result1 = sporulation.germinate_post("My New Post")
        assert result1["created"] is True

        # Try to create same post again
        result2 = sporulation.germinate_post("My New Post")
        assert "error" in result2
        assert "already exists" in result2["error"]


def test_dormant_posts_empty_directory(tmp_path):
    """Test dormant_posts returns empty list when directory is empty."""
    with patch.object(sporulation, 'PUBLISHED_DIR', tmp_path):
        result = sporulation.dormant_posts()
        assert result == []


def test_dormant_posts_lists_posts(tmp_path):
    """Test dormant_posts correctly lists and sorts posts."""
    with patch.object(sporulation, 'PUBLISHED_DIR', tmp_path):
        # Create two test posts
        p1 = tmp_path / "post-one.md"
        p1.write_text("""---
title: "Post One"
pubDatetime: 2024-01-02T00:00:00Z
draft: true
tags: []
---
Post one body.
""")
        p2 = tmp_path / "post-two.md"
        p2.write_text("""---
title: "Post Two"
pubDatetime: 2024-01-01T00:00:00Z
draft: false
tags: []
---
Post two body.
""")
        result = sporulation.dormant_posts()
        assert len(result) == 2
        # Should be sorted with newest first
        assert result[0]["slug"] == "post-one"
        assert result[1]["slug"] == "post-two"
        assert result[0]["draft"] is True
        assert result[1]["draft"] is False
        assert result[0]["words"] == 3


def test_publish_sets_draft_false(tmp_path):
    """Test publish sets draft: false on a post."""
    with patch.object(sporulation, 'PUBLISHED_DIR', tmp_path):
        # Create draft post
        result = sporulation.germinate_post("Test Publish")
        slug = result["slug"]
        path = Path(result["path"])

        # Publish it
        publish_result = sporulation.publish(slug)
        assert publish_result["published"] is True

        # Check the file was updated
        content = path.read_text()
        assert "draft: false" in content
        assert "draft: true" not in content


def test_publish_returns_already_published(tmp_path):
    """Test publish returns already_published when post is already public."""
    with patch.object(sporulation, 'PUBLISHED_DIR', tmp_path):
        sporulation.germinate_post("Test Already Published")
        sporulation.publish("test-already-published")
        # Publish again
        result = sporulation.publish("test-already-published")
        assert result["already_published"] is True


def test_publish_nonexistent_returns_error():
    """Test publish returns error for nonexistent post."""
    result = sporulation.publish("this-post-does-not-exist-at-all")
    assert "error" in result
    assert "No post found" in result["error"]


def test_mutate_post_adds_revision_note(tmp_path):
    """Test mutate_post adds a revision note and updates modDatetime."""
    with patch.object(sporulation, 'PUBLISHED_DIR', tmp_path):
        # Create post
        sporulation.germinate_post("Test Revision")
        # Mutate
        result = sporulation.mutate_post("test-revision", "Fixed typos")
        assert result["revised"] is True

        # Check the file
        path = tmp_path / "test-revision.md"
        content = path.read_text()
        assert 'revisionNote: "Fixed typos"' in content
        assert "modDatetime:" in content


def test_catalog_regenerates_index(tmp_path):
    """Test catalog generates an index file from published posts."""
    with (
        patch.object(sporulation, 'PUBLISHED_DIR', tmp_path),
        patch.object(sporulation, 'INDEX_PATH', tmp_path / "terryli.hm.md")
    ):
        # Create a published post
        post_path = tmp_path / "test-post.md"
        post_path.write_text("""---
title: "Test Blog Post"
description: "A test post"
pubDatetime: 2024-01-01T00:00:00Z
draft: false
tags: [test, blog]
---
This is a test post body.
""")

        result = sporulation.catalog()
        assert result["indexed"] == 1
        index_path = Path(result["path"])
        assert index_path.exists()
        index_content = index_path.read_text()
        assert "terryli.hm" in index_content
        assert "Test Blog Post" in index_content
        assert "test-post" in index_content


def test_propagate_site_returns_error_when_script_missing():
    """Test propagate_site returns error when sync script doesn't exist."""
    with patch.object(sporulation, 'SYNC_SCRIPT', Path("/nonexistent/sync.sh")):
        result = sporulation.propagate_site()
        assert "error" in result
        assert "Sync script not found" in result["error"]


def test_now_iso_format():
    """Test _now_iso returns correctly formatted ISO date."""
    result = sporulation._now_iso()
    # Should look like "2024-01-01T12:00:00.000Z"
    assert len(result) == 24
    assert result.endswith(".000Z")
    assert "T" in result
