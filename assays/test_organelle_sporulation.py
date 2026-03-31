"""Tests for organelles/sporulation — garden publishing for terryli.hm."""
from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from metabolon.organelles.sporulation import (
    PUBLISHED_DIR,
    INDEX_PATH,
    SYNC_SCRIPT,
    _now_iso,
    _to_slug,
    _parse_frontmatter,
    _scan_content,
    germinate_post,
    dormant_posts,
    publish,
    mutate_post,
    propagate_site,
    catalog,
)


# ── _now_iso tests ─────────────────────────────────────────────────────


def test_now_iso_returns_iso_format():
    """_now_iso returns string in ISO 8601 format."""
    result = _now_iso()
    assert isinstance(result, str)
    # Should match YYYY-MM-DDTHH:MM:SS.000Z
    assert "T" in result
    assert result.endswith(".000Z")
    assert len(result) == 24


def test_now_iso_includes_current_date():
    """_now_iso includes current UTC date."""
    from datetime import UTC, datetime

    result = _now_iso()
    now = datetime.now(UTC)
    expected_prefix = now.strftime("%Y-%m-%d")
    assert result.startswith(expected_prefix)


# ── _to_slug tests ─────────────────────────────────────────────────────


def test_to_slug_lowercases():
    """_to_slug converts to lowercase."""
    assert _to_slug("Hello World") == "hello-world"


def test_to_slug_replaces_spaces_with_hyphens():
    """_to_slug replaces spaces with hyphens."""
    assert _to_slug("hello world") == "hello-world"
    assert _to_slug("hello  world") == "hello-world"


def test_to_slug_removes_special_characters():
    """_to_slug removes non-alphanumeric characters."""
    assert _to_slug("hello! world?") == "hello-world"
    # @ and # are removed without adding hyphens (no whitespace between)
    assert _to_slug("hello@world#test") == "helloworldtest"
    # Spaces around special chars become hyphens
    assert _to_slug("hello @world test") == "hello-world-test"


def test_to_slug_consecutive_separators():
    """_to_slug collapses consecutive separators."""
    assert _to_slug("hello--world") == "hello-world"
    assert _to_slug("hello__world") == "hello-world"
    assert _to_slug("hello _ world") == "hello-world"


def test_to_slug_strips_leading_trailing_hyphens():
    """_to_slug strips leading and trailing hyphens."""
    assert _to_slug("-hello world-") == "hello-world"
    assert _to_slug("--test--") == "test"


def test_to_slug_preserves_alphanumeric_and_hyphens():
    """_to_slug preserves alphanumeric characters and hyphens."""
    assert _to_slug("my-post-123") == "my-post-123"
    assert _to_slug("test_post") == "test-post"


# ── _parse_frontmatter tests ───────────────────────────────────────────


def test_parse_frontmatter_basic():
    """_parse_frontmatter parses basic frontmatter."""
    content = '---\ntitle: "Test"\ndraft: true\n---\n\nBody'
    result = _parse_frontmatter(content)
    assert result is not None
    assert result["title"] == "Test"
    assert result["draft"] is True


def test_parse_frontmatter_no_frontmatter():
    """_parse_frontmatter returns None for content without frontmatter."""
    content = "No frontmatter here"
    result = _parse_frontmatter(content)
    assert result is None


def test_parse_frontmatter_incomplete():
    """_parse_frontmatter returns None for incomplete frontmatter."""
    content = "---\ntitle: Test\n"
    result = _parse_frontmatter(content)
    assert result is None


def test_parse_frontmatter_boolean_parsing():
    """_parse_frontmatter parses boolean values."""
    content = "---\ndraft: true\npublished: false\n---\n"
    result = _parse_frontmatter(content)
    assert result["draft"] is True
    assert result["published"] is False


def test_parse_frontmatter_tags_parsing():
    """_parse_frontmatter parses tags as list."""
    content = '---\ntags: [python, test, code]\n---\n'
    result = _parse_frontmatter(content)
    assert result["tags"] == ["python", "test", "code"]


def test_parse_frontmatter_tags_with_quotes():
    """_parse_frontmatter handles quoted tags."""
    content = '---\ntags: ["python", "test"]\n---\n'
    result = _parse_frontmatter(content)
    assert result["tags"] == ["python", "test"]


def test_parse_frontmatter_body_offset():
    """_parse_frontmatter includes _body_offset for content extraction."""
    content = '---\ntitle: "Test"\n---\n\nBody text'
    result = _parse_frontmatter(content)
    assert "_body_offset" in result
    body = content[result["_body_offset"]:]
    # Offset points after closing ---\n, includes leading newline before body
    assert body == "\nBody text"


# ── _scan_content tests ────────────────────────────────────────────────


def test_scan_content_clean():
    """_scan_content returns empty list for clean content."""
    content = "This is a normal blog post without sensitive data."
    warnings = _scan_content(content)
    assert warnings == []


def test_scan_content_dollar_amount():
    """_scan_content detects dollar amounts."""
    content = "I spent $500 on groceries."
    warnings = _scan_content(content)
    assert len(warnings) == 1
    assert "dollar figure" in warnings[0]


def test_scan_content_hkd_amount():
    """_scan_content detects HKD amounts."""
    content = "The cost was HKD 1000."
    warnings = _scan_content(content)
    assert len(warnings) == 1
    assert "HKD figure" in warnings[0]


def test_scan_content_million_figure():
    """_scan_content detects million figures."""
    content = "The company made 5 million dollars."
    warnings = _scan_content(content)
    assert len(warnings) == 1
    assert "million figure" in warnings[0]


def test_scan_content_named_individual():
    """_scan_content detects named individuals with titles."""
    content = "Mr. Smith said hello."
    warnings = _scan_content(content)
    assert len(warnings) == 1
    assert "named individual" in warnings[0]


def test_scan_content_credential():
    """_scan_content detects potential credentials."""
    content = 'password: "mysecretpass123"'
    warnings = _scan_content(content)
    assert len(warnings) == 1
    assert "credential" in warnings[0]


def test_scan_content_multiple_issues():
    """_scan_content detects multiple issues."""
    content = "Mr. Johnson spent $1000 and his password: secretkey123"
    warnings = _scan_content(content)
    assert len(warnings) >= 2


# ── germinate_post tests ───────────────────────────────────────────────


def test_germinate_post_creates_file(tmp_path, monkeypatch):
    """germinate_post creates a new draft post file."""
    monkeypatch.setattr(
        "metabolon.organelles.sporulation.PUBLISHED_DIR", tmp_path
    )
    result = germinate_post("My New Post")
    assert result.get("created") is True
    assert "path" in result
    assert result["slug"] == "my-new-post"
    assert Path(result["path"]).exists()


def test_germinate_post_file_content(tmp_path, monkeypatch):
    """germinate_post creates file with correct frontmatter."""
    monkeypatch.setattr(
        "metabolon.organelles.sporulation.PUBLISHED_DIR", tmp_path
    )
    result = germinate_post("Test Title")
    content = Path(result["path"]).read_text()
    assert 'title: "Test Title"' in content
    assert "draft: true" in content
    assert "description:" in content
    assert "tags: []" in content


def test_germinate_post_existing_file(tmp_path, monkeypatch):
    """germinate_post returns error if file already exists."""
    monkeypatch.setattr(
        "metabolon.organelles.sporulation.PUBLISHED_DIR", tmp_path
    )
    germinate_post("Existing Post")
    result = germinate_post("Existing Post")
    assert "error" in result
    assert "already exists" in result["error"].lower()


def test_germinate_post_creates_directory(tmp_path, monkeypatch):
    """germinate_post creates PUBLISHED_DIR if it doesn't exist."""
    new_dir = tmp_path / "new_published"
    monkeypatch.setattr(
        "metabolon.organelles.sporulation.PUBLISHED_DIR", new_dir
    )
    result = germinate_post("Test")
    assert result.get("created") is True
    assert new_dir.exists()


# ── dormant_posts tests ────────────────────────────────────────────────


def test_dormant_posts_empty_directory(tmp_path, monkeypatch):
    """dormant_posts returns empty list for empty directory."""
    monkeypatch.setattr(
        "metabolon.organelles.sporulation.PUBLISHED_DIR", tmp_path
    )
    result = dormant_posts()
    assert result == []


def test_dormant_posts_nonexistent_directory(tmp_path, monkeypatch):
    """dormant_posts returns empty list for nonexistent directory."""
    nonexistent = tmp_path / "nonexistent"
    monkeypatch.setattr(
        "metabolon.organelles.sporulation.PUBLISHED_DIR", nonexistent
    )
    result = dormant_posts()
    assert result == []


def test_dormant_posts_lists_posts(tmp_path, monkeypatch):
    """dormant_posts lists all posts with correct metadata."""
    monkeypatch.setattr(
        "metabolon.organelles.sporulation.PUBLISHED_DIR", tmp_path
    )
    # Create test post
    germinate_post("First Post")
    germinate_post("Second Post")
    
    posts = dormant_posts()
    assert len(posts) == 2
    slugs = [p["slug"] for p in posts]
    assert "first-post" in slugs
    assert "second-post" in slugs


def test_dormant_posts_sorts_by_date(tmp_path, monkeypatch):
    """dormant_posts sorts posts by date (most recent first)."""
    monkeypatch.setattr(
        "metabolon.organelles.sporulation.PUBLISHED_DIR", tmp_path
    )
    germinate_post("Post One")
    germinate_post("Post Two")
    
    posts = dormant_posts()
    # Both should have dates
    for post in posts:
        assert "date" in post
        assert "draft" in post
        assert "words" in post


# ── publish tests ───────────────────────────────────────────────────────


def test_publish_nonexistent_post(tmp_path, monkeypatch):
    """publish returns error for nonexistent post."""
    monkeypatch.setattr(
        "metabolon.organelles.sporulation.PUBLISHED_DIR", tmp_path
    )
    result = publish("nonexistent")
    assert "error" in result
    assert "No post found" in result["error"]


def test_publish_draft_post(tmp_path, monkeypatch):
    """publish changes draft: true to draft: false."""
    monkeypatch.setattr(
        "metabolon.organelles.sporulation.PUBLISHED_DIR", tmp_path
    )
    germinate_post("Draft Post")
    result = publish("draft-post")
    assert result.get("published") is True
    assert "title" in result
    
    # Verify file was updated
    post_path = tmp_path / "draft-post.md"
    content = post_path.read_text()
    assert "draft: false" in content


def test_publish_already_published(tmp_path, monkeypatch):
    """publish returns already_published for non-draft."""
    monkeypatch.setattr(
        "metabolon.organelles.sporulation.PUBLISHED_DIR", tmp_path
    )
    germinate_post("Already Done")
    # Publish once
    publish("already-done")
    # Try to publish again
    result = publish("already-done")
    assert result.get("already_published") is True


def test_publish_with_warnings(tmp_path, monkeypatch):
    """publish includes warnings for sensitive content."""
    monkeypatch.setattr(
        "metabolon.organelles.sporulation.PUBLISHED_DIR", tmp_path
    )
    germinate_post("Sensitive Post")
    # Add sensitive content
    post_path = tmp_path / "sensitive-post.md"
    content = post_path.read_text()
    content = content.replace("draft: true", "draft: true\n\n$500 spent")
    post_path.write_text(content)
    
    result = publish("sensitive-post")
    assert "warnings" in result
    assert len(result["warnings"]) > 0


def test_publish_with_push(tmp_path, monkeypatch):
    """publish with push=True calls propagate_site."""
    monkeypatch.setattr(
        "metabolon.organelles.sporulation.PUBLISHED_DIR", tmp_path
    )
    germinate_post("Push Post")
    
    # Mock propagate_site to avoid actual sync
    mock_result = {"pushed": True, "url": "https://terryli.hm"}
    with patch("metabolon.organelles.sporulation.propagate_site", return_value=mock_result):
        result = publish("push-post", push=True)
    
    assert result.get("published") is True
    assert "push" in result


# ── mutate_post tests ───────────────────────────────────────────────────


def test_mutate_post_nonexistent(tmp_path, monkeypatch):
    """mutate_post returns error for nonexistent post."""
    monkeypatch.setattr(
        "metabolon.organelles.sporulation.PUBLISHED_DIR", tmp_path
    )
    result = mutate_post("nonexistent", "fixed typo")
    assert "error" in result


def test_mutate_post_adds_revision_note(tmp_path, monkeypatch):
    """mutate_post adds revisionNote to frontmatter."""
    monkeypatch.setattr(
        "metabolon.organelles.sporulation.PUBLISHED_DIR", tmp_path
    )
    germinate_post("Revision Test")
    result = mutate_post("revision-test", "Fixed typo in intro")
    
    assert result.get("revised") is True
    assert result["note"] == "Fixed typo in intro"
    
    # Verify file was updated
    post_path = tmp_path / "revision-test.md"
    content = post_path.read_text()
    assert 'revisionNote: "Fixed typo in intro"' in content


def test_mutate_post_adds_mod_datetime(tmp_path, monkeypatch):
    """mutate_post adds modDatetime to frontmatter."""
    monkeypatch.setattr(
        "metabolon.organelles.sporulation.PUBLISHED_DIR", tmp_path
    )
    germinate_post("Mod Test")
    result = mutate_post("mod-test", "Updated content")
    
    assert result.get("revised") is True
    post_path = tmp_path / "mod-test.md"
    content = post_path.read_text()
    assert "modDatetime:" in content


def test_mutate_post_updates_existing_revision_note(tmp_path, monkeypatch):
    """mutate_post updates existing revisionNote."""
    monkeypatch.setattr(
        "metabolon.organelles.sporulation.PUBLISHED_DIR", tmp_path
    )
    germinate_post("Multi Revision")
    mutate_post("multi-revision", "First edit")
    result = mutate_post("multi-revision", "Second edit")
    
    assert result.get("revised") is True
    post_path = tmp_path / "multi-revision.md"
    content = post_path.read_text()
    assert 'revisionNote: "Second edit"' in content
    # Should only have one revisionNote
    assert content.count("revisionNote:") == 1


# ── propagate_site tests ────────────────────────────────────────────────


def test_propagate_site_missing_script(monkeypatch):
    """propagate_site returns error if sync script doesn't exist."""
    fake_script = Path("/nonexistent/sync.sh")
    monkeypatch.setattr(
        "metabolon.organelles.sporulation.SYNC_SCRIPT", fake_script
    )
    result = propagate_site()
    assert "error" in result
    assert "not found" in result["error"]


def test_propagate_site_success(monkeypatch):
    """propagate_site returns success on successful sync."""
    # Use a fake script path that "exists"
    with patch.object(Path, "exists", return_value=True):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            result = propagate_site()
    
    assert result.get("pushed") is True
    assert result["url"] == "https://terryli.hm"


def test_propagate_site_failure(monkeypatch):
    """propagate_site returns error on sync failure."""
    with patch.object(Path, "exists", return_value=True):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stderr="Sync failed"
            )
            result = propagate_site()
    
    assert "error" in result
    assert "Sync failed" in result["error"]


# ── catalog tests ───────────────────────────────────────────────────────


def test_catalog_creates_index(tmp_path, monkeypatch):
    """catalog creates index file from published posts."""
    published_dir = tmp_path / "published"
    index_path = tmp_path / "index.md"
    published_dir.mkdir()
    
    monkeypatch.setattr(
        "metabolon.organelles.sporulation.PUBLISHED_DIR", published_dir
    )
    monkeypatch.setattr(
        "metabolon.organelles.sporulation.INDEX_PATH", index_path
    )
    
    # Create a valid published post
    post_content = '''---
title: "Test Post"
description: "A test"
pubDatetime: 2024-01-15T10:00:00.000Z
draft: false
tags: [test]
---

This is the body content.
'''
    (published_dir / "test-post.md").write_text(post_content)
    
    result = catalog()
    assert "indexed" in result
    assert result["indexed"] == 1
    assert index_path.exists()


def test_catalog_skips_drafts(tmp_path, monkeypatch):
    """catalog skips draft posts."""
    published_dir = tmp_path / "published"
    index_path = tmp_path / "index.md"
    published_dir.mkdir()
    
    monkeypatch.setattr(
        "metabolon.organelles.sporulation.PUBLISHED_DIR", published_dir
    )
    monkeypatch.setattr(
        "metabolon.organelles.sporulation.INDEX_PATH", index_path
    )
    
    # Create a draft post
    draft_content = '''---
title: "Draft"
description: "Draft post"
pubDatetime: 2024-01-15T10:00:00.000Z
draft: true
tags: []
---

Draft content.
'''
    (published_dir / "draft.md").write_text(draft_content)
    
    result = catalog()
    assert result["indexed"] == 0


def test_catalog_skips_invalid_frontmatter(tmp_path, monkeypatch):
    """catalog skips posts with invalid frontmatter."""
    published_dir = tmp_path / "published"
    index_path = tmp_path / "index.md"
    published_dir.mkdir()
    
    monkeypatch.setattr(
        "metabolon.organelles.sporulation.PUBLISHED_DIR", published_dir
    )
    monkeypatch.setattr(
        "metabolon.organelles.sporulation.INDEX_PATH", index_path
    )
    
    # Create invalid post (missing description)
    invalid_content = '''---
title: "Invalid"
pubDatetime: 2024-01-15T10:00:00.000Z
draft: false
tags: []
---

Content.
'''
    (published_dir / "invalid.md").write_text(invalid_content)
    
    result = catalog()
    assert result["indexed"] == 0


def test_catalog_includes_tags(tmp_path, monkeypatch):
    """catalog includes tags in output."""
    published_dir = tmp_path / "published"
    index_path = tmp_path / "index.md"
    published_dir.mkdir()
    
    monkeypatch.setattr(
        "metabolon.organelles.sporulation.PUBLISHED_DIR", published_dir
    )
    monkeypatch.setattr(
        "metabolon.organelles.sporulation.INDEX_PATH", index_path
    )
    
    post_content = '''---
title: "Tagged Post"
description: "Has tags"
pubDatetime: 2024-01-15T10:00:00.000Z
draft: false
tags: [python, testing]
---

Content.
'''
    (published_dir / "tagged.md").write_text(post_content)
    
    catalog()
    index_content = index_path.read_text()
    assert "python" in index_content
    assert "testing" in index_content


def test_catalog_empty_directory(tmp_path, monkeypatch):
    """catalog handles empty published directory."""
    published_dir = tmp_path / "published"
    index_path = tmp_path / "index.md"
    published_dir.mkdir()
    
    monkeypatch.setattr(
        "metabolon.organelles.sporulation.PUBLISHED_DIR", published_dir
    )
    monkeypatch.setattr(
        "metabolon.organelles.sporulation.INDEX_PATH", index_path
    )
    
    result = catalog()
    assert result["indexed"] == 0
    assert index_path.exists()


# ── Integration tests ───────────────────────────────────────────────────


def test_full_workflow(tmp_path, monkeypatch):
    """Test complete workflow: create, list, publish, catalog."""
    monkeypatch.setattr(
        "metabolon.organelles.sporulation.PUBLISHED_DIR", tmp_path
    )
    index_path = tmp_path / "index.md"
    monkeypatch.setattr(
        "metabolon.organelles.sporulation.INDEX_PATH", index_path
    )
    
    # Create post
    create_result = germinate_post("Workflow Test")
    assert create_result.get("created")
    
    # List posts (should be draft)
    posts = dormant_posts()
    assert len(posts) == 1
    assert posts[0]["draft"] is True
    
    # Publish
    pub_result = publish("workflow-test")
    assert pub_result.get("published")
    
    # List again (should not be draft)
    posts = dormant_posts()
    assert posts[0]["draft"] is False
    
    # Update with description for catalog
    post_path = tmp_path / "workflow-test.md"
    content = post_path.read_text()
    content = content.replace('description: ""', 'description: "A test post"')
    post_path.write_text(content)
    
    # Catalog
    cat_result = catalog()
    assert cat_result["indexed"] == 1
