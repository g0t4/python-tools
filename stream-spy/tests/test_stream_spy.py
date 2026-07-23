"""Tests for stream-spy JSON parsing and formatting."""

import json

from stream_spy.stream_spy import StreamMonitor


class TestParseJson:
    """Tests for the _parse_json method."""

    def setup_method(self) -> None:
        self.monitor = StreamMonitor.__new__(StreamMonitor)

    def test_valid_json_object(self) -> None:
        """Valid JSON object should parse successfully."""
        text = json.dumps({"jsonrpc": "2.0", "method": "initialize"})
        success, parsed = self.monitor._parse_json(text)
        assert success is True
        assert parsed == {"jsonrpc": "2.0", "method": "initialize"}

    def test_valid_json_array(self) -> None:
        """Valid JSON array should parse successfully."""
        text = json.dumps([1, 2, 3])
        success, parsed = self.monitor._parse_json(text)
        assert success is True
        assert parsed == [1, 2, 3]

    def test_valid_json_string(self) -> None:
        """Valid JSON string should parse successfully."""
        text = json.dumps("hello")
        success, parsed = self.monitor._parse_json(text)
        assert success is True
        assert parsed == "hello"

    def test_invalid_json(self) -> None:
        """Invalid JSON should return failure with None."""
        text = "not json at all"
        success, parsed = self.monitor._parse_json(text)
        assert success is False
        assert parsed is None

    def test_partial_json(self) -> None:
        """Partial JSON should return failure with None."""
        text = '{"key": "value", '
        success, parsed = self.monitor._parse_json(text)
        assert success is False
        assert parsed is None

    def test_empty_string(self) -> None:
        """Empty string should return failure with None."""
        text = ""
        success, parsed = self.monitor._parse_json(text)
        assert success is False
        assert parsed is None

    def test_whitespace_only(self) -> None:
        """Whitespace-only string should return failure with None."""
        text = "   \n  "
        success, parsed = self.monitor._parse_json(text)
        assert success is False
        assert parsed is None

    def test_mixed_valid_and_invalid(self) -> None:
        """Each line should be independently validated."""
        valid_line = json.dumps({"id": 1})
        invalid_line = "not json"

        success1, parsed1 = self.monitor._parse_json(valid_line)
        assert success1 is True
        assert parsed1 == {"id": 1}

        success2, parsed2 = self.monitor._parse_json(invalid_line)
        assert success2 is False
        assert parsed2 is None


class TestFormatJson:
    """Tests for the _format_json method."""

    def setup_method(self) -> None:
        self.monitor_compact = StreamMonitor.__new__(StreamMonitor)
        self.monitor_compact._expand_json = False

        self.monitor_expand = StreamMonitor.__new__(StreamMonitor)
        self.monitor_expand._expand_json = True

    def test_compact_format(self) -> None:
        """Compact mode should produce single-line JSON."""
        obj = {"jsonrpc": "2.0", "method": "initialize", "params": {"key": "value"}}
        result = self.monitor_compact._format_json(obj)
        assert "\n" not in result
        assert json.loads(result) == obj

    def test_expand_format(self) -> None:
        """Expand mode should produce multi-line pretty-printed JSON."""
        obj = {"jsonrpc": "2.0", "method": "initialize", "params": {"key": "value"}}
        result = self.monitor_expand._format_json(obj)
        assert "\n" in result
        assert json.loads(result) == obj

    def test_expand_format_has_indentation(self) -> None:
        """Expanded JSON should be indented."""
        obj = {"a": {"b": 1}}
        result = self.monitor_expand._format_json(obj)
        lines = result.strip().split("\n")
        assert len(lines) > 1

    def test_simple_value_compact(self) -> None:
        """Simple values should work in compact mode."""
        result = self.monitor_compact._format_json("hello")
        assert result == json.dumps("hello")

    def test_simple_value_expand(self) -> None:
        """Simple values should work in expand mode."""
        result = self.monitor_expand._format_json("hello")
        assert result == json.dumps("hello") + "\n"


class TestFileLogger:
    """Tests for the FileLogger class."""

    def test_file_logger_creates_directory(self, tmp_path) -> None:
        """FileLogger should create parent directories if they don't exist."""
        from stream_spy.stream_spy import FileLogger

        log_file = tmp_path / "subdir" / "logs" / "output.log"
        logger = FileLogger(log_file)
        # Should not raise
        logger._filepath.parent.mkdir(parents=True, exist_ok=True)
        logger._file = open(log_file, "w", encoding="utf-8")
        logger.write_raw("test line\n")
        logger._file.close()

        assert log_file.exists()
        assert log_file.read_text() == "test line\n"
