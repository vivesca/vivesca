"""Tests for v2 stall detection — streaming-json action parsing.

v1 (current): diff-hash only. Kills after 5 consecutive identical hashes (~2.5 min).
v2 (this): parse CC's streaming-json output for 5 OpenHands stall patterns.
  Diff-hash becomes one signal among several, not the sole kill trigger.

The stall detector should:
1. Parse streaming-json lines from ribosome stdout
2. Detect 5 stall patterns (repeated action, repeated error, monologue, ping-pong, context error)
3. Use graduated response (warn first, kill second)
4. Still use diff-hash as a supplementary signal (not primary)
"""

from __future__ import annotations


class TestStallPatternDetection:
    """Detect the 5 OpenHands stall patterns from streaming-json events."""

    def test_detect_repeated_action(self):
        """Same tool call 4+ times in a row = stall."""
        from polysome.stall_detector import detect_stall_pattern

        events = [
            {"type": "tool_use", "name": "Read", "input": {"path": "/foo/bar.py"}},
            {"type": "tool_use", "name": "Read", "input": {"path": "/foo/bar.py"}},
            {"type": "tool_use", "name": "Read", "input": {"path": "/foo/bar.py"}},
            {"type": "tool_use", "name": "Read", "input": {"path": "/foo/bar.py"}},
        ]
        result = detect_stall_pattern(events)
        assert result is not None
        assert result["pattern"] == "repeated_action"

    def test_no_stall_on_different_actions(self):
        """Different tool calls are not a stall."""
        from polysome.stall_detector import detect_stall_pattern

        events = [
            {"type": "tool_use", "name": "Read", "input": {"path": "/foo/a.py"}},
            {"type": "tool_use", "name": "Edit", "input": {"path": "/foo/a.py"}},
            {"type": "tool_use", "name": "Read", "input": {"path": "/foo/a.py"}},
            {"type": "tool_use", "name": "Bash", "input": {"command": "pytest"}},
        ]
        result = detect_stall_pattern(events)
        assert result is None

    def test_detect_repeated_error(self):
        """Same error message 3+ times = stall."""
        from polysome.stall_detector import detect_stall_pattern

        events = [
            {"type": "tool_result", "error": "ModuleNotFoundError: No module named 'foo'"},
            {"type": "tool_result", "error": "ModuleNotFoundError: No module named 'foo'"},
            {"type": "tool_result", "error": "ModuleNotFoundError: No module named 'foo'"},
        ]
        result = detect_stall_pattern(events)
        assert result is not None
        assert result["pattern"] == "repeated_error"

    def test_detect_ping_pong(self):
        """Alternating between 2 actions 6+ cycles = stall."""
        from polysome.stall_detector import detect_stall_pattern

        events = []
        for _ in range(6):
            events.append({"type": "tool_use", "name": "Edit", "input": {"old": "a", "new": "b"}})
            events.append({"type": "tool_use", "name": "Edit", "input": {"old": "b", "new": "a"}})
        result = detect_stall_pattern(events)
        assert result is not None
        assert result["pattern"] == "ping_pong"

    def test_detect_monologue(self):
        """Reasoning without acting 3+ times = stall."""
        from polysome.stall_detector import detect_stall_pattern

        events = [
            {"type": "text", "content": "Let me think about this..."},
            {"type": "text", "content": "Actually, I should consider..."},
            {"type": "text", "content": "On second thought, maybe..."},
        ]
        result = detect_stall_pattern(events)
        assert result is not None
        assert result["pattern"] == "monologue"


class TestGraduatedResponse:
    """Stall detection uses graduated response — warn first, kill second."""

    def test_first_detection_is_warning(self):
        """First stall detection returns 'warn', not 'kill'."""
        from polysome.stall_detector import StallDetector

        detector = StallDetector()
        action = detector.on_stall_detected({"pattern": "repeated_action"})
        assert action == "warn"

    def test_second_detection_is_kill(self):
        """Second stall detection after warning returns 'kill'."""
        from polysome.stall_detector import StallDetector

        detector = StallDetector()
        detector.on_stall_detected({"pattern": "repeated_action"})
        action = detector.on_stall_detected({"pattern": "repeated_action"})
        assert action == "kill"

    def test_different_pattern_resets_warning(self):
        """A different stall pattern resets the warning counter."""
        from polysome.stall_detector import StallDetector

        detector = StallDetector()
        detector.on_stall_detected({"pattern": "repeated_action"})
        action = detector.on_stall_detected({"pattern": "repeated_error"})
        assert action == "warn"  # Different pattern, reset


class TestDiffHashAsSupplementary:
    """Diff-hash is one signal, not the sole trigger."""

    def test_frozen_diff_alone_does_not_kill(self):
        """Frozen diff hash without other stall signals = warn only."""
        from polysome.stall_detector import StallDetector

        detector = StallDetector()
        # Simulate 5 frozen diff hashes
        for _ in range(5):
            detector.record_diff_hash("abc123")
        action = detector.evaluate()
        assert action in ("warn", None)  # Not immediate kill

    def test_frozen_diff_plus_pattern_kills(self):
        """Frozen diff hash + detected stall pattern = kill."""
        from polysome.stall_detector import StallDetector

        detector = StallDetector()
        for _ in range(5):
            detector.record_diff_hash("abc123")
        detector.on_stall_detected({"pattern": "repeated_action"})
        action = detector.evaluate()
        assert action == "kill"
