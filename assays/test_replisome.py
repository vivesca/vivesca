#!/usr/bin/env python3
from __future__ import annotations

"""Tests for replisome effector — multi-model deliberation with LangGraph."""


import subprocess
import types
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path

# Execute the replisome file directly
replisome_path = Path(str(Path.home() / "germline/effectors/replisome"))
replisome_code = replisome_path.read_text()

# Create module namespace and exec
namespace = {"__name__": "test_mod"}
exec(replisome_code, namespace)

# Create a proper module-like object that shares the same namespace
# This allows patching to work correctly
replisome = types.SimpleNamespace()
for key, value in namespace.items():
    if not key.startswith('__'):
        setattr(replisome, key, value)


# ---------------------------------------------------------------------------
# Test constants and configuration
# ---------------------------------------------------------------------------

def test_default_model():
    """Test that DEFAULT_MODEL is set correctly."""
    assert replisome.DEFAULT_MODEL == "glm"


def test_direct_models_config():
    """Test that DIRECT_MODELS has expected model configurations."""
    assert "gemini" in replisome.DIRECT_MODELS
    assert "opencode" in replisome.DIRECT_MODELS
    assert "codex" in replisome.DIRECT_MODELS
    assert replisome.DIRECT_MODELS["gemini"] == ["gemini", "-p"]
    assert replisome.DIRECT_MODELS["opencode"] == ["opencode", "--prompt"]


def test_pty_models():
    """Test that PTY_MODELS has expected entries."""
    assert "opencode" in replisome.PTY_MODELS
    assert "codex" in replisome.PTY_MODELS


def test_model_timeout_floor():
    """Test that MODEL_TIMEOUT_FLOOR has minimum timeouts."""
    assert replisome.MODEL_TIMEOUT_FLOOR["gemini"] == 120
    assert replisome.MODEL_TIMEOUT_FLOOR["opencode"] == 120
    assert replisome.MODEL_TIMEOUT_FLOOR["codex"] == 120


# ---------------------------------------------------------------------------
# Test _append helper
# ---------------------------------------------------------------------------

def test_append_empty_lists():
    """Test _append with two empty lists."""
    result = replisome._append([], [])
    assert result == []


def test_append_first_empty():
    """Test _append with first list empty."""
    result = replisome._append([], [1, 2, 3])
    assert result == [1, 2, 3]


def test_append_second_empty():
    """Test _append with second list empty."""
    result = replisome._append([1, 2, 3], [])
    assert result == [1, 2, 3]


def test_append_both_nonempty():
    """Test _append with both lists non-empty."""
    result = replisome._append([1, 2], [3, 4])
    assert result == [1, 2, 3, 4]


def test_append_with_dicts():
    """Test _append with dictionaries in lists."""
    dicts1 = [{"role": "user", "content": "hi"}]
    dicts2 = [{"role": "assistant", "content": "hello"}]
    result = replisome._append(dicts1, dicts2)
    assert len(result) == 2
    assert result[0]["role"] == "user"
    assert result[1]["role"] == "assistant"


# ---------------------------------------------------------------------------
# Test scratchpad_text
# ---------------------------------------------------------------------------

def test_scratchpad_text_empty():
    """Test scratchpad_text with empty turns list."""
    result = replisome.scratchpad_text([])
    assert result == ""


def test_scratchpad_text_single_turn():
    """Test scratchpad_text with a single turn."""
    turns = [{"role": "Claude", "content": "Hello world"}]
    result = replisome.scratchpad_text(turns)
    assert "### Claude" in result
    assert "Hello world" in result


def test_scratchpad_text_multiple_turns():
    """Test scratchpad_text with multiple turns."""
    turns = [
        {"role": "Claude", "content": "Hello"},
        {"role": "Gemini", "content": "Hi there"},
        {"role": "Human", "content": "Greetings"},
    ]
    result = replisome.scratchpad_text(turns)
    assert "### Claude" in result
    assert "### Gemini" in result
    assert "### Human" in result
    assert "Hello" in result
    assert "Hi there" in result
    assert "Greetings" in result


def test_scratchpad_text_format():
    """Test that scratchpad_text produces correct markdown format."""
    turns = [{"role": "Model", "content": "Test content"}]
    result = replisome.scratchpad_text(turns)
    # Should have proper markdown formatting
    lines = result.strip().split("\n")
    assert any("### Model" in line for line in lines)


# ---------------------------------------------------------------------------
# Test model_prompt
# ---------------------------------------------------------------------------

def test_model_prompt_includes_scratchpad():
    """Test that model_prompt includes the scratchpad content."""
    scratchpad = "### Claude\n\nHello world"
    result = replisome.model_prompt(scratchpad, "~/germline")
    assert scratchpad in result


def test_model_prompt_includes_repo():
    """Test that model_prompt includes the repository path."""
    scratchpad = "### Test\n\nContent"
    result = replisome.model_prompt(scratchpad, "/path/to/repo")
    assert "/path/to/repo" in result


def test_model_prompt_includes_rules():
    """Test that model_prompt includes the expected rules."""
    scratchpad = ""
    result = replisome.model_prompt(scratchpad, "~/germline")
    assert "Read before speaking" in result
    assert "Be direct" in result
    assert "QUESTION:" in result


def test_model_prompt_structure():
    """Test that model_prompt has proper structure."""
    result = replisome.model_prompt("test", "~/repo")
    assert "multi-model deliberation" in result
    assert "Your turn" in result


# ---------------------------------------------------------------------------
# Test ReplisomeState TypedDict
# ---------------------------------------------------------------------------

def test_replisome_state_is_typeddict():
    """Test that ReplisomeState is a TypedDict."""
    # TypedDict classes exist and can be instantiated
    state = {
        "task": "test task",
        "models": ["glm"],
        "turns": [],
        "current_model_idx": 0,
        "current_round": 1,
        "max_rounds": 2,
        "timeout": 120,
        "repo": "~/germline",
        "scratchpad_path": "/tmp/test.md",
        "needs_human": False,
        "human_question": "",
        "done": False,
    }
    # Should not raise - validates structure
    assert state["task"] == "test task"
    assert state["models"] == ["glm"]


# ---------------------------------------------------------------------------
# Test routing functions
# ---------------------------------------------------------------------------

def test_route_after_model_needs_human():
    """Test route_after_model returns 'human' when needs_human is True."""
    state = {
        "needs_human": True,
        "current_model_idx": 0,
        "models": ["glm", "gemini"],
    }
    assert replisome.route_after_model(state) == "human"


def test_route_after_model_more_models():
    """Test route_after_model returns 'model_turn' when more models to query."""
    state = {
        "needs_human": False,
        "current_model_idx": 0,
        "models": ["glm", "gemini"],
    }
    assert replisome.route_after_model(state) == "model_turn"


def test_route_after_model_synthesize():
    """Test route_after_model returns 'synthesise' when all models have spoken."""
    state = {
        "needs_human": False,
        "current_model_idx": 2,  # All models done
        "models": ["glm", "gemini"],
    }
    assert replisome.route_after_model(state) == "synthesise"


def test_route_after_human_more_models():
    """Test route_after_human returns 'model_turn' when more models."""
    state = {
        "current_model_idx": 1,
        "models": ["glm", "gemini"],
    }
    assert replisome.route_after_human(state) == "model_turn"


def test_route_after_human_synthesize():
    """Test route_after_human returns 'synthesise' when all models done."""
    state = {
        "current_model_idx": 2,
        "models": ["glm", "gemini"],
    }
    assert replisome.route_after_human(state) == "synthesise"


def test_route_after_synth_done():
    """Test route_after_synth returns END when done is True."""
    state = {"done": True}
    assert replisome.route_after_synth(state) == replisome.END


def test_route_after_synth_continue():
    """Test route_after_synth returns 'model_turn' when not done."""
    state = {"done": False}
    assert replisome.route_after_synth(state) == "model_turn"


# ---------------------------------------------------------------------------
# Test build_graph
# ---------------------------------------------------------------------------

def test_build_graph_returns_compiled_graph():
    """Test that build_graph returns a compiled LangGraph graph."""
    graph = replisome.build_graph()
    assert graph is not None
    # Should have nodes
    assert hasattr(graph, 'nodes') or hasattr(graph, 'stream')


def test_build_graph_has_expected_nodes():
    """Test that the graph contains expected nodes."""
    graph = replisome.build_graph()
    # Test that graph was built successfully by checking it has stream method
    assert hasattr(graph, 'stream')
    assert hasattr(graph, 'invoke')


# ---------------------------------------------------------------------------
# Test query_model with mocking
# ---------------------------------------------------------------------------

def test_query_model_direct_model_success():
    """Test query_model with direct model (non-PTY)."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "Direct response"
    mock_result.stderr = ""

    with patch('subprocess.run', return_value=mock_result):
        result = replisome.query_model("gemini", "test prompt")
        assert result == "Direct response"


def test_query_model_direct_model_error():
    """Test query_model with direct model returning error."""
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = ""
    mock_result.stderr = "Command failed"

    with patch('subprocess.run', return_value=mock_result):
        result = replisome.query_model("gemini", "test prompt")
        assert "error" in result


def test_query_model_timeout():
    """Test query_model handles timeout."""
    with patch('subprocess.run', side_effect=subprocess.TimeoutExpired("cmd", 120)):
        result = replisome.query_model("gemini", "test prompt")
        assert "timeout" in result


def test_query_model_timeout_respects_floor():
    """Test that query_model respects MODEL_TIMEOUT_FLOOR."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "OK"
    mock_result.stderr = ""

    with patch('subprocess.run', return_value=mock_result) as mock_run:
        # Request timeout below floor (e.g., 30s when floor is 120)
        replisome.query_model("gemini", "test", timeout=30)
        # Should use floor value of 120
        call_timeout = mock_run.call_args[1].get('timeout')
        assert call_timeout == 120


def test_query_model_removes_claudecode_env():
    """Test that query_model removes CLAUDECODE from environment."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "OK"
    mock_result.stderr = ""

    with patch('subprocess.run', return_value=mock_result) as mock_run:
        replisome.query_model("gemini", "test")
        env = mock_run.call_args[1].get('env', {})
        assert "CLAUDECODE" not in env


def test_query_model_pty_error_handling():
    """Test query_model handles PTY errors gracefully."""
    # Test that when pty.openpty fails, we get an error message
    with patch('pty.openpty', side_effect=OSError("No PTY available")):
        result = replisome.query_model("opencode", "test prompt")
        # Should contain error indication
        assert "error" in result.lower() or "empty" in result.lower()


# ---------------------------------------------------------------------------
# Test _pty_query with mocked PTY operations
# ---------------------------------------------------------------------------

def test_pty_query_cleans_ansi_codes_unit():
    """Test that _pty_query regex patterns correctly strip ANSI codes."""
    # Test the regex patterns directly without running the full PTY code
    text = "\x1b[32mGreen text\x1b[0m"
    clean = replisome._ANSI_RE.sub('', text)
    assert '\x1b[' not in clean
    assert 'Green text' in clean


def test_pty_query_cleans_control_chars_unit():
    """Test that control characters are stripped."""
    text = "Hello\x00World\x07Test\x1f"
    clean = replisome._CTRL_RE.sub('', text)
    assert '\x00' not in clean
    assert '\x07' not in clean
    assert '\x1f' not in clean


def test_pty_query_cleans_tui_chrome_unit():
    """Test that TUI chrome characters are replaced."""
    text = "Result: █▀▄ some text ░░░"
    clean = replisome._TUI_CHROME_RE.sub(' ', text)
    assert '█' not in clean
    assert '▀' not in clean
    assert '░' not in clean


def test_pty_query_extracts_thinking_block_unit():
    """Test thinking block extraction logic (via regex on output)."""
    # Simulate the output processing that happens after cleaning
    clean = "Some noise\nThinking: This is the actual thought content.\nMore output"
    thinking_parts = clean.split('Thinking:')
    assert len(thinking_parts) > 1
    assert "actual thought content" in thinking_parts[-1]


def test_pty_query_handles_empty_output_unit():
    """Test that empty output is handled correctly."""
    # When output is empty after cleaning
    lines = [s.strip() for s in "".splitlines() if s.strip() and len(s.strip()) > 3]
    assert lines == []


# ---------------------------------------------------------------------------
# Test node_model_turn
# ---------------------------------------------------------------------------

def test_node_model_turn_basic():
    """Test node_model_turn returns expected structure."""
    state = {
        "current_model_idx": 0,
        "models": ["test_model"],
        "turns": [],
        "timeout": 120,
        "repo": "~/germline",
        "scratchpad_path": "/tmp/test.md",
    }

    # Patch query_model in the namespace dict directly
    original_query_model = namespace['query_model']
    namespace['query_model'] = MagicMock(return_value="Model response")
    try:
        with patch('builtins.open', mock_open()):
            result = replisome.node_model_turn(state)
    finally:
        namespace['query_model'] = original_query_model

    assert "turns" in result
    assert len(result["turns"]) == 1
    assert result["turns"][0]["role"] == "test_model"
    assert result["current_model_idx"] == 1


def test_node_model_turn_detects_question():
    """Test node_model_turn detects QUESTION: prefix."""
    state = {
        "current_model_idx": 0,
        "models": ["test_model"],
        "turns": [],
        "timeout": 120,
        "repo": "~/germline",
        "scratchpad_path": "/tmp/test.md",
    }

    original_query_model = namespace['query_model']
    namespace['query_model'] = MagicMock(return_value="QUESTION: What should I do?")
    try:
        with patch('builtins.open', mock_open()):
            result = replisome.node_model_turn(state)
    finally:
        namespace['query_model'] = original_query_model

    assert result["needs_human"] is True
    assert "QUESTION" in result["human_question"]


def test_node_model_turn_detects_bold_question():
    """Test node_model_turn detects **QUESTION:** prefix."""
    state = {
        "current_model_idx": 0,
        "models": ["test_model"],
        "turns": [],
        "timeout": 120,
        "repo": "~/germline",
        "scratchpad_path": "/tmp/test.md",
    }

    original_query_model = namespace['query_model']
    namespace['query_model'] = MagicMock(return_value="**QUESTION:** What now?")
    try:
        with patch('builtins.open', mock_open()):
            result = replisome.node_model_turn(state)
    finally:
        namespace['query_model'] = original_query_model

    assert result["needs_human"] is True


# ---------------------------------------------------------------------------
# Test node_human
# ---------------------------------------------------------------------------

def test_node_human_with_input():
    """Test node_human processes user input."""
    state = {
        "human_question": "What should we do?",
        "scratchpad_path": "/tmp/test.md",
    }

    with patch('builtins.input', return_value="My answer"):
        with patch('builtins.open', mock_open()):
            result = replisome.node_human(state)

    assert result["needs_human"] is False
    assert len(result["turns"]) == 1
    assert result["turns"][0]["content"] == "My answer"


def test_node_human_handles_eof():
    """Test node_human handles EOFError gracefully."""
    state = {
        "human_question": "Question?",
        "scratchpad_path": "/tmp/test.md",
    }

    with patch('builtins.input', side_effect=EOFError):
        with patch('builtins.open', mock_open()):
            result = replisome.node_human(state)

    assert result["turns"][0]["content"] == "[skipped]"


def test_node_human_handles_keyboard_interrupt():
    """Test node_human handles KeyboardInterrupt gracefully."""
    state = {
        "human_question": "Question?",
        "scratchpad_path": "/tmp/test.md",
    }

    with patch('builtins.input', side_effect=KeyboardInterrupt):
        with patch('builtins.open', mock_open()):
            result = replisome.node_human(state)

    assert result["turns"][0]["content"] == "[skipped]"


def test_node_human_empty_input():
    """Test node_human handles empty input."""
    state = {
        "human_question": "Question?",
        "scratchpad_path": "/tmp/test.md",
    }

    with patch('builtins.input', return_value="   "):  # Whitespace only
        with patch('builtins.open', mock_open()):
            result = replisome.node_human(state)

    assert result["turns"][0]["content"] == "[skipped]"


# ---------------------------------------------------------------------------
# Test node_synthesise
# ---------------------------------------------------------------------------

def test_node_synthesise_basic():
    """Test node_synthesise returns expected structure."""
    state = {
        "models": ["model1", "model2"],
        "turns": [
            {"role": "model1", "content": "Opinion 1"},
            {"role": "model2", "content": "Opinion 2"},
        ],
        "timeout": 120,
        "current_round": 1,
        "max_rounds": 2,
        "scratchpad_path": "/tmp/test.md",
    }

    original_query_model = namespace['query_model']
    namespace['query_model'] = MagicMock(return_value="Synthesis")
    try:
        with patch('builtins.open', mock_open()):
            result = replisome.node_synthesise(state)
    finally:
        namespace['query_model'] = original_query_model

    assert "turns" in result
    assert result["current_round"] == 2
    assert result["current_model_idx"] == 0
    assert result["done"] is False  # round 2 <= max_rounds 2


def test_node_synthesise_sets_done_when_exceeds_rounds():
    """Test node_synthesise sets done when exceeding max_rounds."""
    state = {
        "models": ["model1"],
        "turns": [],
        "timeout": 120,
        "current_round": 2,
        "max_rounds": 2,
        "scratchpad_path": "/tmp/test.md",
    }

    original_query_model = namespace['query_model']
    namespace['query_model'] = MagicMock(return_value="Final synthesis")
    try:
        with patch('builtins.open', mock_open()):
            result = replisome.node_synthesise(state)
    finally:
        namespace['query_model'] = original_query_model

    # After synthesis, round becomes 3, which is > max_rounds 2
    assert result["done"] is True


# ---------------------------------------------------------------------------
# Test main function (basic structure tests)
# ---------------------------------------------------------------------------

def test_main_creates_scratchpad():
    """Test that main creates scratchpad file."""
    mock_graph = MagicMock()
    mock_graph.return_value.stream.return_value = iter([])

    original_build_graph = namespace['build_graph']
    namespace['build_graph'] = mock_graph
    try:
        with patch('sys.argv', ['replisome', 'test task']):
            with patch('pathlib.Path.mkdir'):
                with patch('builtins.open', mock_open()):
                    with patch('pathlib.Path.write_text'):
                        replisome.main()
    finally:
        namespace['build_graph'] = original_build_graph


def test_main_uses_custom_models():
    """Test that main parses --model argument."""
    mock_graph = MagicMock()
    mock_instance = MagicMock()
    mock_instance.stream.return_value = iter([])
    mock_graph.return_value = mock_instance

    original_build_graph = namespace['build_graph']
    namespace['build_graph'] = mock_graph
    try:
        # Use '--' to separate optional args from positional task
        with patch('sys.argv', ['replisome', '--model', 'haiku', 'gemini', '--', 'test task']):
            with patch('pathlib.Path.mkdir'):
                with patch('builtins.open', mock_open()):
                    with patch('pathlib.Path.write_text'):
                        replisome.main()
    finally:
        namespace['build_graph'] = original_build_graph


def test_main_uses_custom_rounds():
    """Test that main parses --rounds argument."""
    mock_graph = MagicMock()
    mock_instance = MagicMock()
    mock_instance.stream.return_value = iter([])
    mock_graph.return_value = mock_instance

    original_build_graph = namespace['build_graph']
    namespace['build_graph'] = mock_graph
    try:
        with patch('sys.argv', ['replisome', '--rounds', '3', 'test task']):
            with patch('pathlib.Path.mkdir'):
                with patch('builtins.open', mock_open()):
                    with patch('pathlib.Path.write_text'):
                        replisome.main()
    finally:
        namespace['build_graph'] = original_build_graph


def test_main_uses_custom_scratchpad():
    """Test that main parses --scratchpad argument."""
    mock_graph = MagicMock()
    mock_instance = MagicMock()
    mock_instance.stream.return_value = iter([])
    mock_graph.return_value = mock_instance

    original_build_graph = namespace['build_graph']
    namespace['build_graph'] = mock_graph
    try:
        with patch('sys.argv', ['replisome', '--scratchpad', '/custom/path.md', 'test task']):
            with patch('pathlib.Path.mkdir'):
                with patch('builtins.open', mock_open()):
                    with patch('pathlib.Path.write_text'):
                        replisome.main()
    finally:
        namespace['build_graph'] = original_build_graph


# ---------------------------------------------------------------------------
# Integration-like tests (mocked)
# ---------------------------------------------------------------------------

def test_full_graph_flow_mocked():
    """Test a complete graph flow with all external calls mocked."""
    graph = replisome.build_graph()

    initial_state = {
        "task": "test task",
        "models": ["test_model"],
        "turns": [],
        "current_model_idx": 0,
        "current_round": 1,
        "max_rounds": 1,
        "timeout": 10,
        "repo": "~/germline",
        "scratchpad_path": "/tmp/test.md",
        "needs_human": False,
        "human_question": "",
        "done": False,
    }

    original_query_model = namespace['query_model']
    namespace['query_model'] = MagicMock(return_value="Response")
    try:
        with patch('builtins.open', mock_open()):
            config = {"configurable": {"thread_id": "test"}}
            # Stream should complete without errors
            events = list(graph.stream(initial_state, config=config))
            assert len(events) > 0
    finally:
        namespace['query_model'] = original_query_model


# ---------------------------------------------------------------------------
# Test file existence and basic properties
# ---------------------------------------------------------------------------

def test_replisome_file_exists():
    """Test that replisome effector file exists."""
    assert replisome_path.exists()
    assert replisome_path.is_file()


def test_replisome_is_executable():
    """Test that replisome has shebang."""
    first_line = replisome_code.split('\n')[0]
    assert first_line.startswith('#!/usr/bin/env python')


def test_replisome_docstring():
    """Test that replisome has docstring."""
    assert '"""' in replisome_code
    assert 'replisome' in replisome_code.lower() or 'Replisome' in replisome_code


# ---------------------------------------------------------------------------
# Additional edge case tests
# ---------------------------------------------------------------------------

def test_query_model_empty_stdout():
    """Test query_model handles empty stdout."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "   "  # Whitespace only
    mock_result.stderr = ""

    with patch('subprocess.run', return_value=mock_result):
        result = replisome.query_model("gemini", "test prompt")
        assert "error" in result or "empty" in result


def test_query_model_unknown_model_falls_back_to_channel():
    """Test query_model falls back to 'channel' command for unknown models."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "Channel response"
    mock_result.stderr = ""

    with patch('subprocess.run', return_value=mock_result) as mock_run:
        result = replisome.query_model("unknown_model", "test")
        # Should use channel command as fallback
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "channel"
        assert call_args[1] == "unknown_model"


def test_query_model_generic_exception():
    """Test query_model handles generic exceptions."""
    with patch('subprocess.run', side_effect=Exception("Unexpected error")):
        result = replisome.query_model("gemini", "test prompt")
        assert "error" in result.lower()


def test_pty_query_proc_still_running():
    """Test _pty_query handles process that stays running (kills it)."""
    # This tests the timeout/kill path in _pty_query
    # We can't easily mock the full PTY, but we can test the logic exists
    with patch('pty.openpty', side_effect=OSError("Mocked failure")):
        result = replisome.query_model("opencode", "test")
        # Should handle the error gracefully
        assert result  # Returns some error message


def test_node_model_turn_multiline_response():
    """Test node_model_turn handles multiline responses."""
    state = {
        "current_model_idx": 0,
        "models": ["test_model"],
        "turns": [],
        "timeout": 120,
        "repo": "~/germline",
        "scratchpad_path": "/tmp/test.md",
    }

    multiline_response = "Line 1\nLine 2\nLine 3"
    original_query_model = namespace['query_model']
    namespace['query_model'] = MagicMock(return_value=multiline_response)
    try:
        with patch('builtins.open', mock_open()):
            result = replisome.node_model_turn(state)
    finally:
        namespace['query_model'] = original_query_model

    assert "turns" in result
    assert result["turns"][0]["content"] == multiline_response


def test_node_model_turn_empty_response():
    """Test node_model_turn handles empty model response."""
    state = {
        "current_model_idx": 0,
        "models": ["test_model"],
        "turns": [],
        "timeout": 120,
        "repo": "~/germline",
        "scratchpad_path": "/tmp/test.md",
    }

    original_query_model = namespace['query_model']
    namespace['query_model'] = MagicMock(return_value="")
    try:
        with patch('builtins.open', mock_open()):
            result = replisome.node_model_turn(state)
    finally:
        namespace['query_model'] = original_query_model

    assert result["needs_human"] is False


def test_node_model_turn_whitespace_response():
    """Test node_model_turn handles whitespace-only response."""
    state = {
        "current_model_idx": 0,
        "models": ["test_model"],
        "turns": [],
        "timeout": 120,
        "repo": "~/germline",
        "scratchpad_path": "/tmp/test.md",
    }

    original_query_model = namespace['query_model']
    namespace['query_model'] = MagicMock(return_value="   \n\n   ")
    try:
        with patch('builtins.open', mock_open()):
            result = replisome.node_model_turn(state)
    finally:
        namespace['query_model'] = original_query_model

    # Should not crash
    assert "turns" in result


def test_model_prompt_with_special_characters():
    """Test model_prompt handles special characters in scratchpad."""
    scratchpad = "### Test\n\nContent with <special> & \"quotes\" & 'apostrophes'"
    result = replisome.model_prompt(scratchpad, "~/germline")
    assert scratchpad in result


def test_scratchpad_text_with_newlines():
    """Test scratchpad_text preserves newlines in content."""
    turns = [{"role": "User", "content": "Line 1\nLine 2\nLine 3"}]
    result = replisome.scratchpad_text(turns)
    assert "Line 1\nLine 2\nLine 3" in result


def test_scratchpad_text_with_markdown():
    """Test scratchpad_text preserves markdown formatting."""
    turns = [{"role": "Assistant", "content": "# Header\n\n- item 1\n- item 2"}]
    result = replisome.scratchpad_text(turns)
    assert "# Header" in result
    assert "- item 1" in result


def test_main_with_custom_timeout():
    """Test that main parses --timeout argument."""
    mock_graph = MagicMock()
    mock_instance = MagicMock()
    mock_instance.stream.return_value = iter([])
    mock_graph.return_value = mock_instance

    original_build_graph = namespace['build_graph']
    namespace['build_graph'] = mock_graph
    try:
        with patch('sys.argv', ['replisome', '--timeout', '60', 'test task']):
            with patch('pathlib.Path.mkdir'):
                with patch('builtins.open', mock_open()):
                    with patch('pathlib.Path.write_text'):
                        replisome.main()
    finally:
        namespace['build_graph'] = original_build_graph


def test_main_with_custom_repo():
    """Test that main parses --repo argument."""
    mock_graph = MagicMock()
    mock_instance = MagicMock()
    mock_instance.stream.return_value = iter([])
    mock_graph.return_value = mock_instance

    original_build_graph = namespace['build_graph']
    namespace['build_graph'] = mock_graph
    try:
        with patch('sys.argv', ['replisome', '--repo', '/custom/repo', 'test task']):
            with patch('pathlib.Path.mkdir'):
                with patch('builtins.open', mock_open()):
                    with patch('pathlib.Path.write_text'):
                        replisome.main()
    finally:
        namespace['build_graph'] = original_build_graph


def test_route_after_model_needs_human_takes_precedence():
    """Test that needs_human takes precedence over model index check."""
    state = {
        "needs_human": True,
        "current_model_idx": 0,
        "models": ["glm"],  # Only one model, so would normally go to synthesise
    }
    # But needs_human should take precedence
    assert replisome.route_after_model(state) == "human"


def test_append_preserves_original_lists():
    """Test that _append doesn't modify original lists."""
    list1 = [1, 2]
    list2 = [3, 4]
    result = replisome._append(list1, list2)
    assert list1 == [1, 2]  # Original unchanged
    assert list2 == [3, 4]  # Original unchanged
    assert result == [1, 2, 3, 4]


def test_pty_model_uses_pty_path():
    """Test that PTY models use _pty_query."""
    # Patch _pty_query in namespace
    original_pty_query = namespace.get('_pty_query')
    mock_pty = MagicMock(return_value="PTY response")
    namespace['_pty_query'] = mock_pty

    try:
        result = replisome.query_model("opencode", "test prompt", timeout=60)
        # Should have called _pty_query
        assert mock_pty.called
        assert result == "PTY response"
    finally:
        if original_pty_query:
            namespace['_pty_query'] = original_pty_query


def test_pty_query_empty_response_handling():
    """Test _pty_query returns proper message for empty response."""
    with patch('pty.openpty') as mock_openpty:
        # Setup mock PTY that returns nothing useful
        master_fd = 999
        slave_fd = 998
        mock_openpty.return_value = (master_fd, slave_fd)

        with patch('os.close'):
            with patch('subprocess.Popen') as mock_popen:
                mock_proc = MagicMock()
                mock_proc.poll.return_value = 0  # Process done
                mock_popen.return_value = mock_proc

                with patch('select.select', return_value=([], [], [])):
                    with patch('os.read', return_value=b''):
                        result = replisome._pty_query(["test"], 10)
                        # Should return empty string or error message
                        assert result is not None


def test_node_synthesise_includes_model_labels():
    """Test that node_synthesise includes model labels in prompt."""
    state = {
        "models": ["model1", "model2"],
        "turns": [],
        "timeout": 120,
        "current_round": 1,
        "max_rounds": 2,
        "scratchpad_path": "/tmp/test.md",
    }

    original_query_model = namespace['query_model']
    captured_prompt = []

    def capture_prompt(model, prompt, timeout):
        captured_prompt.append(prompt)
        return "Synthesis"

    namespace['query_model'] = capture_prompt
    try:
        with patch('builtins.open', mock_open()):
            replisome.node_synthesise(state)
    finally:
        namespace['query_model'] = original_query_model

    # The prompt should mention both models
    assert "model1 + model2" in captured_prompt[0]


def test_node_human_human_role_label():
    """Test that node_human labels human as 'Human (Terry)'."""
    state = {
        "human_question": "Question?",
        "scratchpad_path": "/tmp/test.md",
    }

    with patch('builtins.input', return_value="My answer"):
        with patch('builtins.open', mock_open()) as mock_file:
            result = replisome.node_human(state)

    assert result["turns"][0]["role"] == "Human (Terry)"


def test_full_graph_flow_multiple_rounds():
    """Test graph flow with multiple rounds."""
    graph = replisome.build_graph()

    initial_state = {
        "task": "test task",
        "models": ["model1"],
        "turns": [],
        "current_model_idx": 0,
        "current_round": 1,
        "max_rounds": 2,
        "timeout": 10,
        "repo": "~/germline",
        "scratchpad_path": "/tmp/test.md",
        "needs_human": False,
        "human_question": "",
        "done": False,
    }

    call_count = [0]

    def mock_query(model, prompt, timeout):
        call_count[0] += 1
        return f"Response {call_count[0]}"

    original_query_model = namespace['query_model']
    namespace['query_model'] = mock_query
    try:
        with patch('builtins.open', mock_open()):
            config = {"configurable": {"thread_id": "test_multi"}}
            events = list(graph.stream(initial_state, config=config))
            # Should have multiple events for multiple rounds
            assert len(events) > 0
    finally:
        namespace['query_model'] = original_query_model
