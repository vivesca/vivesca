"""Tests for gap_junction enzyme module."""

from unittest.mock import patch

from metabolon.enzymes.gap_junction import gap_junction, GapJunctionResult


def test_gap_junction_unknown_action():
    """Test unknown action returns error message."""
    result = gap_junction(action="invalid")
    assert isinstance(result, GapJunctionResult)
    assert "Unknown action" in result.output
    assert "Valid: read, search, draft, list_chats, sync_status" in result.output


def test_gap_junction_read_missing_name():
    """Test read without required name returns error."""
    result = gap_junction(action="read")
    assert result.output == "read requires: name"


def test_gap_junction_search_missing_query():
    """Test search without required query returns error."""
    result = gap_junction(action="search")
    assert result.output == "search requires: query"


def test_gap_junction_draft_missing_params():
    """Test draft missing name or message returns error."""
    result = gap_junction(action="draft", name="test")
    assert result.output == "draft requires: name, message"
    
    result = gap_junction(action="draft", message="test")
    assert result.output == "draft requires: name, message"


@patch("metabolon.enzymes.gap_junction.receive_signals")
def test_gap_junction_read_success_close_contact(mock_receive):
    """Test read action with valid name for close contact adds prefix."""
    mock_receive.return_value = "2024-03-01 10:00:00  tara: Hello there\n2024-03-01 10:05:00  me: Hi!"
    
    result = gap_junction(action="read", name="tara", limit=10)
    
    mock_receive.assert_called_once_with("tara", 10)
    assert isinstance(result, GapJunctionResult)
    assert result.output.startswith("[gap_junction] ")
    assert "Hello there" in result.output


@patch("metabolon.enzymes.gap_junction.receive_signals")
def test_gap_junction_read_success_other_contact(mock_receive):
    """Test read action with non-close contact doesn't add prefix."""
    mock_receive.return_value = "No messages found"
    
    result = gap_junction(action="read", name="john", limit=5)
    
    mock_receive.assert_called_once_with("john", 5)
    assert not result.output.startswith("[gap_junction] ")
    assert result.output == "No messages found"


@patch("metabolon.enzymes.gap_junction.search_signals")
def test_gap_junction_search_global(mock_search):
    """Test search action without name scope."""
    mock_search.return_value = "Found 3 messages"
    
    result = gap_junction(action="search", query="meeting", limit=10)
    
    mock_search.assert_called_once_with("meeting", "", 10)
    assert result.output == "Found 3 messages"


@patch("metabolon.enzymes.gap_junction.search_signals")
def test_gap_junction_search_scoped(mock_search):
    """Test search action with name scope."""
    mock_search.return_value = "Found 1 message"
    
    result = gap_junction(action="search", query="lunch", name="dad", limit=5)
    
    mock_search.assert_called_once_with("lunch", "dad", 5)
    assert result.output == "Found 1 message"


@patch("metabolon.enzymes.gap_junction.compose_signal")
def test_gap_junction_draft_success(mock_compose):
    """Test draft action produces command."""
    expected_cmd = "wacli send --to '123456789@s.whatsapp.net' 'Hello world'"
    mock_compose.return_value = expected_cmd
    
    result = gap_junction(action="draft", name="yujie", message="Hello world")
    
    mock_compose.assert_called_once_with("yujie", "Hello world")
    assert result.output == expected_cmd


@patch("metabolon.enzymes.gap_junction.active_junctions")
def test_gap_junction_list_chats(mock_active):
    """Test list_chats action delegates."""
    mock_active.return_value = "Chat 1\nChat 2\nChat 3"
    
    result = gap_junction(action="list_chats", limit=3)
    
    mock_active.assert_called_once_with(3)
    assert result.output == "Chat 1\nChat 2\nChat 3"


@patch("metabolon.enzymes.gap_junction.junction_status")
def test_gap_junction_sync_status(mock_status):
    """Test sync_status action delegates."""
    mock_status.return_value = "Sync daemon is running"
    
    result = gap_junction(action="sync_status")
    
    mock_status.assert_called_once()
    assert result.output == "Sync daemon is running"


def test_action_case_insensitive():
    """Test action is case-insensitive."""
    # Should work regardless of case
    with patch("metabolon.enzymes.gap_junction.receive_signals") as mock:
        mock.return_value = "test"
        result = gap_junction(action="READ", name="tara")
        assert result.output == "[gap_junction] test"
        
    with patch("metabolon.enzymes.gap_junction.receive_signals") as mock:
        mock.return_value = "test"
        result = gap_junction(action="Read", name="tara")
        assert result.output == "[gap_junction] test"
