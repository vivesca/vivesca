from __future__ import annotations

"""Tests for metabolon.organelles.praxis — Praxis.md TODO list management."""

from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest

from metabolon.organelles import praxis


# ── Fixtures ───────────────────────────────────────────────────────────────


@pytest.fixture
def mock_today_date():
    """Mock _today_date to return a fixed date."""
    with patch.object(praxis, "_today_date") as mock:
        mock.return_value = date(2025, 6, 15)  # A Sunday
        yield mock


@pytest.fixture
def mock_read_all():
    """Mock _read_all to return sample data."""
    with patch.object(praxis, "_read_all") as mock:
        yield mock


@pytest.fixture
def mock_read_today():
    """Mock _read_today to return sample data."""
    with patch.object(praxis, "_read_today") as mock:
        yield mock


def make_item(
    text: str = "Task",
    done: bool = False,
    due: str | None = None,
    when: str | None = None,
    agent: str | None = None,
    recurring: str | None = None,
    raw: str | None = None,
    section: str = "Inbox",
) -> dict:
    """Create a sample TODO item dict."""
    item = {
        "text": text,
        "raw": raw or text,
        "done": done,
        "section": section,
        "due": due,
        "when": when,
        "agent": agent,
        "recurring": recurring,
        "tags": {},
    }
    if due:
        item["tags"]["due"] = due
    if when:
        item["tags"]["when"] = when
    if agent:
        item["tags"]["agent"] = agent
    if recurring:
        item["tags"]["recurring"] = recurring
    return item


# ── _parse_date tests ──────────────────────────────────────────────────────


def test_parse_date_valid():
    """_parse_date parses YYYY-MM-DD format correctly."""
    result = praxis._parse_date("2025-06-15")
    assert result == date(2025, 6, 15)


def test_parse_date_with_whitespace():
    """_parse_date handles leading/trailing whitespace."""
    result = praxis._parse_date("  2025-06-15  ")
    assert result == date(2025, 6, 15)


def test_parse_date_none_input():
    """_parse_date returns None for None input."""
    assert praxis._parse_date(None) is None


def test_parse_date_empty_string():
    """_parse_date returns None for empty string."""
    assert praxis._parse_date("") is None


def test_parse_date_invalid_format():
    """_parse_date returns None for invalid format."""
    assert praxis._parse_date("15-06-2025") is None
    assert praxis._parse_date("June 15, 2025") is None
    assert praxis._parse_date("not-a-date") is None


# ── _is_overdue tests ──────────────────────────────────────────────────────


def test_is_overdue_true():
    """_is_overdue returns True for past due date."""
    item = make_item(due="2025-06-10")
    assert praxis._is_overdue(item, date(2025, 6, 15)) is True


def test_is_overdue_today_not_overdue():
    """_is_overdue returns False for due date of today."""
    item = make_item(due="2025-06-15")
    assert praxis._is_overdue(item, date(2025, 6, 15)) is False


def test_is_overdue_future_not_overdue():
    """_is_overdue returns False for future due date."""
    item = make_item(due="2025-06-20")
    assert praxis._is_overdue(item, date(2025, 6, 15)) is False


def test_is_overdue_no_due_date():
    """_is_overdue returns False when no due date."""
    item = make_item()
    assert praxis._is_overdue(item, date(2025, 6, 15)) is False


def test_is_overdue_done_item():
    """_is_overdue checks due date regardless of done status."""
    item = make_item(done=True, due="2025-06-10")
    # Still overdue by date, even if done
    assert praxis._is_overdue(item, date(2025, 6, 15)) is True


# ── today() tests ───────────────────────────────────────────────────────────


def test_today_returns_items(mock_today_date, mock_read_today):
    """today() returns items from _read_today."""
    mock_read_today.return_value = {
        "available": True,
        "items": [
            make_item(text="Task 1", due="2025-06-15"),
            make_item(text="Task 2", due="2025-06-10"),  # overdue
        ],
    }
    result = praxis.today()
    assert result["date"] == "2025-06-15"
    assert result["today_count"] == 2
    assert result["overdue_count"] == 1


def test_today_empty_items(mock_today_date, mock_read_today):
    """today() returns empty list when no items."""
    mock_read_today.return_value = {"available": True, "items": []}
    result = praxis.today()
    assert result["items"] == []
    assert result["today_count"] == 0
    assert result["overdue_count"] == 0


def test_today_unavailable_returns_error(mock_read_today):
    """today() returns error dict when data unavailable."""
    mock_read_today.return_value = {
        "available": False,
        "error": "file not found",
        "items": [],
    }
    result = praxis.today()
    assert "error" in result
    assert result["error"] == "file not found"


# ── upcoming() tests ────────────────────────────────────────────────────────


def test_upcoming_returns_items_in_range(mock_today_date, mock_read_all):
    """upcoming() returns items within the date range."""
    mock_read_all.return_value = {
        "available": True,
        "items": [
            make_item(text="Today", due="2025-06-15"),
            make_item(text="Tomorrow", due="2025-06-16"),
            make_item(text="Next week", due="2025-06-20"),
            make_item(text="Out of range", due="2025-07-01"),
        ],
    }
    result = praxis.upcoming(days=7)
    assert result["total_count"] == 3  # Today, Tomorrow, Next week


def test_upcoming_excludes_done_items(mock_today_date, mock_read_all):
    """upcoming() excludes completed items."""
    mock_read_all.return_value = {
        "available": True,
        "items": [
            make_item(text="Done task", done=True, due="2025-06-15"),
            make_item(text="Open task", done=False, due="2025-06-16"),
        ],
    }
    result = praxis.upcoming(days=7)
    assert result["total_count"] == 1
    assert result["items"][0]["text"] == "Open task"


def test_upcoming_excludes_someday_items(mock_today_date, mock_read_all):
    """upcoming() excludes someday items."""
    mock_read_all.return_value = {
        "available": True,
        "items": [
            make_item(text="Someday task", due="2025-06-16", raw="Someday task `someday`"),
            make_item(text="Regular task", due="2025-06-16"),
        ],
    }
    result = praxis.upcoming(days=7)
    assert result["total_count"] == 1
    assert result["items"][0]["text"] == "Regular task"


def test_upcoming_includes_when_date(mock_today_date, mock_read_all):
    """upcoming() includes items with 'when' date in range."""
    mock_read_all.return_value = {
        "available": True,
        "items": [
            make_item(text="Scheduled task", when="2025-06-17"),
        ],
    }
    result = praxis.upcoming(days=7)
    assert result["total_count"] == 1


def test_upcoming_sorts_by_date(mock_today_date, mock_read_all):
    """upcoming() sorts items by earliest relevant date."""
    mock_read_all.return_value = {
        "available": True,
        "items": [
            make_item(text="Later", due="2025-06-20"),
            make_item(text="Sooner", due="2025-06-16"),
        ],
    }
    result = praxis.upcoming(days=7)
    assert result["items"][0]["text"] == "Sooner"
    assert result["items"][1]["text"] == "Later"


def test_upcoming_custom_days(mock_today_date, mock_read_all):
    """upcoming() respects custom days parameter."""
    mock_read_all.return_value = {
        "available": True,
        "items": [
            make_item(text="In range", due="2025-06-18"),
            make_item(text="Out of range", due="2025-06-25"),
        ],
    }
    result = praxis.upcoming(days=3)
    assert result["total_count"] == 1


def test_upcoming_unavailable_returns_error(mock_read_all):
    """upcoming() returns error when data unavailable."""
    mock_read_all.return_value = {"available": False, "error": "no file", "items": []}
    result = praxis.upcoming()
    assert "error" in result


# ── overdue() tests ─────────────────────────────────────────────────────────


def test_overdue_returns_past_due_items(mock_today_date, mock_read_all):
    """overdue() returns items with due date before today."""
    mock_read_all.return_value = {
        "available": True,
        "items": [
            make_item(text="Overdue 1", due="2025-06-10"),
            make_item(text="Overdue 2", due="2025-06-05"),
            make_item(text="Today", due="2025-06-15"),
            make_item(text="Future", due="2025-06-20"),
        ],
    }
    result = praxis.overdue()
    assert result["total_count"] == 2
    assert result["overdue_count"] == 2


def test_overdue_excludes_done_items(mock_today_date, mock_read_all):
    """overdue() excludes completed items."""
    mock_read_all.return_value = {
        "available": True,
        "items": [
            make_item(text="Done overdue", done=True, due="2025-06-10"),
            make_item(text="Open overdue", done=False, due="2025-06-10"),
        ],
    }
    result = praxis.overdue()
    assert result["total_count"] == 1


def test_overdue_excludes_no_due_date(mock_today_date, mock_read_all):
    """overdue() excludes items without due date."""
    mock_read_all.return_value = {
        "available": True,
        "items": [
            make_item(text="No due date"),
        ],
    }
    result = praxis.overdue()
    assert result["total_count"] == 0


def test_overdue_sorts_by_date(mock_today_date, mock_read_all):
    """overdue() sorts items by due date."""
    mock_read_all.return_value = {
        "available": True,
        "items": [
            make_item(text="More overdue", due="2025-06-01"),
            make_item(text="Less overdue", due="2025-06-10"),
        ],
    }
    result = praxis.overdue()
    assert result["items"][0]["text"] == "More overdue"
    assert result["items"][1]["text"] == "Less overdue"


def test_overdue_unavailable_returns_error(mock_read_all):
    """overdue() returns error when data unavailable."""
    mock_read_all.return_value = {"available": False, "error": "no file", "items": []}
    result = praxis.overdue()
    assert "error" in result


# ── someday() tests ─────────────────────────────────────────────────────────


def test_someday_returns_tagged_items(mock_today_date, mock_read_all):
    """someday() returns items with someday tag."""
    mock_read_all.return_value = {
        "available": True,
        "items": [
            make_item(text="Someday task", raw="Someday task `someday`"),
            make_item(text="Regular task", raw="Regular task"),
        ],
    }
    result = praxis.someday()
    assert result["total_count"] == 1
    assert result["items"][0]["text"] == "Someday task"


def test_someday_excludes_done_items(mock_today_date, mock_read_all):
    """someday() excludes completed items."""
    mock_read_all.return_value = {
        "available": True,
        "items": [
            make_item(text="Done someday", done=True, raw="Done someday `someday`"),
            make_item(text="Open someday", done=False, raw="Open someday `someday`"),
        ],
    }
    result = praxis.someday()
    assert result["total_count"] == 1


def test_someday_counts_overdue(mock_today_date, mock_read_all):
    """someday() counts overdue items in overdue_count."""
    mock_read_all.return_value = {
        "available": True,
        "items": [
            make_item(
                text="Overdue someday",
                due="2025-06-01",
                raw="Overdue someday `someday`",
            ),
            make_item(text="Future someday", raw="Future someday `someday`"),
        ],
    }
    result = praxis.someday()
    assert result["overdue_count"] == 1


def test_someday_unavailable_returns_error(mock_read_all):
    """someday() returns error when data unavailable."""
    mock_read_all.return_value = {"available": False, "error": "no file", "items": []}
    result = praxis.someday()
    assert "error" in result


# ── all_items() tests ───────────────────────────────────────────────────────


def test_all_items_returns_incomplete(mock_today_date, mock_read_all):
    """all_items() returns all incomplete items."""
    mock_read_all.return_value = {
        "available": True,
        "items": [
            make_item(text="Open task"),
            make_item(text="Done task", done=True),
        ],
    }
    result = praxis.all_items()
    assert result["total_count"] == 1
    assert result["items"][0]["text"] == "Open task"


def test_all_items_counts_overdue(mock_today_date, mock_read_all):
    """all_items() counts overdue items."""
    mock_read_all.return_value = {
        "available": True,
        "items": [
            make_item(text="Overdue", due="2025-06-01"),
            make_item(text="Future", due="2025-06-20"),
        ],
    }
    result = praxis.all_items()
    assert result["overdue_count"] == 1


def test_all_items_unavailable_returns_error(mock_read_all):
    """all_items() returns error when data unavailable."""
    mock_read_all.return_value = {"available": False, "error": "no file", "items": []}
    result = praxis.all_items()
    assert "error" in result


# ── spare() tests ───────────────────────────────────────────────────────────


def test_spare_returns_section_items(mock_today_date):
    """spare() returns items from Spare Capacity section."""
    with patch("metabolon.pinocytosis.recall_todo") as mock_recall:
        mock_recall.return_value = {
            "available": True,
            "items": [
                make_item(text="Spare task 1"),
                make_item(text="Spare task 2"),
            ],
        }
        result = praxis.spare()
        assert result["total_count"] == 2
        mock_recall.assert_called_once_with(sections=["Spare Capacity"])


def test_spare_excludes_done_items(mock_today_date):
    """spare() excludes completed items."""
    with patch("metabolon.pinocytosis.recall_todo") as mock_recall:
        mock_recall.return_value = {
            "available": True,
            "items": [
                make_item(text="Done spare", done=True),
                make_item(text="Open spare", done=False),
            ],
        }
        result = praxis.spare()
        assert result["total_count"] == 1


def test_spare_unavailable_returns_error(mock_today_date):
    """spare() returns error when data unavailable."""
    with patch("metabolon.pinocytosis.recall_todo") as mock_recall:
        mock_recall.return_value = {"available": False, "error": "no file", "items": []}
        result = praxis.spare()
        assert "error" in result


# ── clean() tests ───────────────────────────────────────────────────────────


def test_clean_no_praxis_file():
    """clean() returns error when Praxis.md doesn't exist."""
    mock_praxis = MagicMock()
    mock_praxis.exists.return_value = False
    with patch("metabolon.organelles.praxis.PRAXIS", mock_praxis):
        result = praxis.clean()
        assert "error" in result
        assert result["error"] == "No Praxis.md found"


def test_clean_no_completed_items():
    """clean() returns empty when no completed items."""
    praxis_content = """# Inbox

- [ ] Task 1
- [ ] Task 2
"""
    mock_praxis = MagicMock()
    mock_praxis.exists.return_value = True
    mock_praxis.read_text.return_value = praxis_content
    mock_archive = MagicMock()
    mock_archive.exists.return_value = False
    with (
        patch("metabolon.organelles.praxis.PRAXIS", mock_praxis),
        patch("metabolon.organelles.praxis.PRAXIS_ARCHIVE", mock_archive),
    ):
        result = praxis.clean()
        assert result["archived"] == 0
        assert result["items"] == []
        mock_praxis.write_text.assert_not_called()


def test_clean_archives_completed_items():
    """clean() archives completed items and stamps them."""
    praxis_content = """# Inbox

- [x] Completed task
- [ ] Open task
"""
    archive_content = """# Archive

## May 2025

- [x] Old completed
"""
    mock_praxis = MagicMock()
    mock_praxis.exists.return_value = True
    mock_praxis.read_text.return_value = praxis_content
    mock_archive = MagicMock()
    mock_archive.exists.return_value = True
    mock_archive.read_text.return_value = archive_content
    with (
        patch("metabolon.organelles.praxis.PRAXIS", mock_praxis),
        patch("metabolon.organelles.praxis.PRAXIS_ARCHIVE", mock_archive),
        patch("metabolon.organelles.praxis.datetime") as mock_dt,
    ):
        mock_dt.now.return_value.strftime.side_effect = lambda fmt: {
            "%Y-%m-%d": "2025-06-15",
            "%B %Y": "June 2025",
        }[fmt]
        result = praxis.clean()

        assert result["archived"] == 1
        assert "Completed task" in result["items"][0]
        assert "done:2025-06-15" in result["items"][0]
        mock_praxis.write_text.assert_called_once()
        mock_archive.write_text.assert_called_once()


def test_clean_adds_done_stamp_if_missing():
    """clean() adds done:YYYY-MM-DD to items without it."""
    praxis_content = "- [x] Task without stamp\n"
    mock_praxis = MagicMock()
    mock_praxis.exists.return_value = True
    mock_praxis.read_text.return_value = praxis_content
    mock_archive = MagicMock()
    mock_archive.exists.return_value = False
    mock_archive.read_text.return_value = ""
    with (
        patch("metabolon.organelles.praxis.PRAXIS", mock_praxis),
        patch("metabolon.organelles.praxis.PRAXIS_ARCHIVE", mock_archive),
        patch("metabolon.organelles.praxis.datetime") as mock_dt,
    ):
        mock_dt.now.return_value.strftime.side_effect = lambda fmt: {
            "%Y-%m-%d": "2025-06-15",
            "%B %Y": "June 2025",
        }[fmt]
        result = praxis.clean()
        assert "done:2025-06-15" in result["items"][0]


def test_clean_preserves_existing_done_stamp():
    """clean() preserves existing done: stamp."""
    praxis_content = "- [x] Task `done:2025-05-01`\n"
    mock_praxis = MagicMock()
    mock_praxis.exists.return_value = True
    mock_praxis.read_text.return_value = praxis_content
    mock_archive = MagicMock()
    mock_archive.exists.return_value = False
    mock_archive.read_text.return_value = ""
    with (
        patch("metabolon.organelles.praxis.PRAXIS", mock_praxis),
        patch("metabolon.organelles.praxis.PRAXIS_ARCHIVE", mock_archive),
        patch("metabolon.organelles.praxis.datetime") as mock_dt,
    ):
        mock_dt.now.return_value.strftime.side_effect = lambda fmt: {
            "%Y-%m-%d": "2025-06-15",
            "%B %Y": "June 2025",
        }[fmt]
        result = praxis.clean()
        assert "done:2025-05-01" in result["items"][0]
        assert "done:2025-06-15" not in result["items"][0]


def test_clean_skips_children_of_completed():
    """clean() skips child items of completed parent."""
    praxis_content = """- [x] Parent task
  - Child item 1
  - Child item 2
- [ ] Next task
"""
    mock_praxis = MagicMock()
    mock_praxis.exists.return_value = True
    mock_praxis.read_text.return_value = praxis_content
    mock_archive = MagicMock()
    mock_archive.exists.return_value = False
    mock_archive.read_text.return_value = ""
    with (
        patch("metabolon.organelles.praxis.PRAXIS", mock_praxis),
        patch("metabolon.organelles.praxis.PRAXIS_ARCHIVE", mock_archive),
        patch("metabolon.organelles.praxis.datetime") as mock_dt,
    ):
        mock_dt.now.return_value.strftime.side_effect = lambda fmt: {
            "%Y-%m-%d": "2025-06-15",
            "%B %Y": "June 2025",
        }[fmt]
        praxis.clean()
        written = mock_praxis.write_text.call_args[0][0]
        assert "Child item" not in written
        assert "Next task" in written


def test_clean_creates_month_header_if_missing():
    """clean() creates month header in archive if not present."""
    praxis_content = "- [x] Completed\n"
    archive_content = """# Archive

## May 2025

Old items
"""
    mock_praxis = MagicMock()
    mock_praxis.exists.return_value = True
    mock_praxis.read_text.return_value = praxis_content
    mock_archive = MagicMock()
    mock_archive.exists.return_value = True
    mock_archive.read_text.return_value = archive_content
    with (
        patch("metabolon.organelles.praxis.PRAXIS", mock_praxis),
        patch("metabolon.organelles.praxis.PRAXIS_ARCHIVE", mock_archive),
        patch("metabolon.organelles.praxis.datetime") as mock_dt,
    ):
        mock_dt.now.return_value.strftime.side_effect = lambda fmt: {
            "%Y-%m-%d": "2025-06-15",
            "%B %Y": "June 2025",
        }[fmt]
        praxis.clean()
        written = mock_archive.write_text.call_args[0][0]
        assert "## June 2025" in written


# ── stats() tests ───────────────────────────────────────────────────────────


def test_stats_counts_total(mock_today_date, mock_read_all):
    """stats() counts total incomplete items."""
    mock_read_all.return_value = {
        "available": True,
        "items": [
            make_item(text="Task 1"),
            make_item(text="Task 2"),
            make_item(text="Done", done=True),
        ],
    }
    result = praxis.stats()
    assert result["total"] == 2


def test_stats_counts_overdue(mock_today_date, mock_read_all):
    """stats() counts overdue items."""
    mock_read_all.return_value = {
        "available": True,
        "items": [
            make_item(text="Overdue", due="2025-06-01"),
            make_item(text="Today", due="2025-06-15"),
            make_item(text="Future", due="2025-06-20"),
        ],
    }
    result = praxis.stats()
    assert result["overdue"] == 1


def test_stats_counts_due_this_week(mock_today_date, mock_read_all):
    """stats() counts items due within 7 days."""
    mock_read_all.return_value = {
        "available": True,
        "items": [
            make_item(text="Today", due="2025-06-15"),
            make_item(text="This week", due="2025-06-18"),
            make_item(text="Next week", due="2025-06-25"),
        ],
    }
    result = praxis.stats()
    assert result["due_this_week"] == 2


def test_stats_counts_someday(mock_today_date, mock_read_all):
    """stats() counts someday items."""
    mock_read_all.return_value = {
        "available": True,
        "items": [
            make_item(text="Someday", raw="Someday `someday`"),
            make_item(text="Regular"),
        ],
    }
    result = praxis.stats()
    assert result["someday"] == 1


def test_stats_counts_by_agent(mock_today_date, mock_read_all):
    """stats() counts items by agent."""
    mock_read_all.return_value = {
        "available": True,
        "items": [
            make_item(text="Claude task", agent="claude"),
            make_item(text="Terry task", agent="terry"),
            make_item(text="No agent"),
        ],
    }
    result = praxis.stats()
    assert result["symbiont_stimuli"] == 1
    assert result["host_stimuli"] == 1


def test_stats_counts_recurring(mock_today_date, mock_read_all):
    """stats() counts recurring items."""
    mock_read_all.return_value = {
        "available": True,
        "items": [
            make_item(text="Daily", recurring="daily"),
            make_item(text="Non-recurring"),
        ],
    }
    result = praxis.stats()
    assert result["recurring"] == 1


def test_stats_unavailable_returns_error(mock_read_all):
    """stats() returns error when data unavailable."""
    mock_read_all.return_value = {"available": False, "error": "no file", "items": []}
    result = praxis.stats()
    assert "error" in result


def test_stats_all_zeros_when_empty(mock_today_date, mock_read_all):
    """stats() returns all zeros when no items."""
    mock_read_all.return_value = {"available": True, "items": []}
    result = praxis.stats()
    assert result["total"] == 0
    assert result["overdue"] == 0
    assert result["due_this_week"] == 0
    assert result["someday"] == 0
    assert result["symbiont_stimuli"] == 0
    assert result["host_stimuli"] == 0
    assert result["recurring"] == 0
