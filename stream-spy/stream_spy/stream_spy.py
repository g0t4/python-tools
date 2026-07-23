"""StreamSpy - Intercept and monitor subprocess streams.

Wraps around calling another application, intercepting stdin/stdout/stderr,
and providing beautiful monitoring with JSON parsing and syntax highlighting.

Designed primarily for wrapping MCP STDIO servers to intercept and monitor
communication between clients and servers.
"""

import asyncio
import json
import signal
import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Any


class FileLogger:
    """Handles writing intercepted streams to a log file."""

    def __init__(self, filepath: Path) -> None:
        self._filepath = filepath
        self._file: Any = None

    async def open(self) -> None:
        """Open the log file for writing."""
        self._filepath.parent.mkdir(parents=True, exist_ok=True)
        self._file = open(self._filepath, "w", encoding="utf-8")

    def write_raw(self, text: str) -> None:
        """Write raw text to the log file."""
        if self._file is not None:
            self._file.write(text)
            self._file.flush()

    async def close(self) -> None:
        """Close the log file."""
        if self._file is not None:
            self._file.close()
            self._file = None


class StreamMonitor:
    """Intercepts and monitors streams from a subprocess.

    Reads from stdin/stdout/stderr, optionally parses JSON with syntax
    highlighting, and writes to both console and an optional log file.
    """

    def __init__(
        self,
        process: asyncio.subprocess.Process,
        *,
        stdin_json: bool = False,
        stdout_json: bool = False,
        stderr_json: bool = False,
        expand_json: bool = False,
        file_logger: FileLogger | None = None,
    ) -> None:
        self._process = process
        self._stdin_json = stdin_json
        self._stdout_json = stdout_json
        self._stderr_json = stderr_json
        self._expand_json = expand_json
        self._file_logger = file_logger

    def _parse_json(self, text: str) -> tuple[bool, Any | None]:
        """Try to parse text as JSON.

        Returns:
            Tuple of (is_valid, parsed_object_or_None).
        """
        try:
            return True, json.loads(text)
        except (json.JSONDecodeError, ValueError):
            return False, None

    def _format_json(self, obj: Any) -> str:
        """Format a JSON object for display."""
        if self._expand_json:
            return json.dumps(obj, indent=2) + "\n"
        return json.dumps(obj)

    async def _process_stream(
        self,
        reader: asyncio.StreamReader,
        json_mode: bool,
        prefix: str,
    ) -> None:
        """Process a stream line by line."""
        while True:
            try:
                line = await reader.readline()
                if not line:
                    break
                line_str = line.decode("utf-8", errors="replace")
                self._write_to_console(line_str, prefix)
                self._log_raw(line_str)
                if json_mode:
                    success, parsed = self._parse_json(line_str)
                    if success:
                        formatted = self._format_json(parsed)
                        self._write_json_output(formatted)
                    else:
                        self._write_parse_error(line_str)
            except asyncio.CancelledError:
                break

    def _write_to_console(self, text: str, prefix: str) -> None:
        """Write text to console with a colored prefix."""
        from rich.console import Console
        from rich.text import Text

        console = Console()
        full_line = Text(prefix + text.rstrip("\n"))
        console.print(full_line)

    def _write_json_output(self, formatted: str) -> None:
        """Write formatted JSON to console using rich syntax highlighting."""
        from rich.console import Console
        from rich.json import JSON

        console = Console()
        json_obj = json.loads(formatted)
        indent = 2 if self._expand_json else None
        console.print(JSON.from_data(json_obj, indent=indent))

    def _write_parse_error(self, line_str: str) -> None:
        """Write parse error indicator to console."""
        from rich.console import Console
        from rich.text import Text

        console = Console()
        error_text = Text("⚠️  JSON parse error: ")
        error_text.append(line_str.rstrip("\n"), style="bold red")
        console.print(error_text)

    def _log_raw(self, text: str) -> None:
        """Write raw text to the log file if logging is enabled."""
        if self._file_logger is not None:
            self._file_logger.write_raw(text)

    async def run(self) -> None:
        """Run all stream monitoring tasks concurrently."""
        # Handle stdin - read from sys.stdin and forward to subprocess
        await self._handle_stdin()

        # Handle stdout and stderr concurrently
        stdout_task = asyncio.create_task(
            self._process_stream(self._process.stdout, self._stdout_json, "<<< OUT: ")
        )
        stderr_task = asyncio.create_task(
            self._process_stream(self._process.stderr, self._stderr_json, "<<< ERR: ")
        )

        await asyncio.gather(stdout_task, stderr_task)

    async def _handle_stdin(self) -> None:
        """Read from sys.stdin and forward to subprocess stdin."""
        loop = asyncio.get_running_loop()

        def read_stdin_lines() -> list[str]:
            """Read all lines from stdin in a thread."""
            lines: list[str] = []
            for line in sys.stdin:
                lines.append(line)
            return lines

        try:
            stdin_lines = await loop.run_in_executor(None, read_stdin_lines)
        except (BrokenPipeError, OSError):
            return

        if not stdin_lines:
            # No input - just close stdin
            if self._process.stdin:
                self._process.stdin.close()
            return

        # Write each line to both console and subprocess
        for line in stdin_lines:
            line_str = line.rstrip("\n")
            self._write_to_console(line, ">>> IN: ")
            self._log_raw(line)
            if self._stdin_json:
                success, parsed = self._parse_json(line)
                if success:
                    formatted = self._format_json(parsed)
                    self._write_json_output(formatted)
                else:
                    self._write_parse_error(line)
            # Forward to subprocess
            if self._process.stdin is not None:
                try:
                    self._process.stdin.write(line.encode("utf-8"))
                except (BrokenPipeError, RuntimeError):
                    break

        # Close stdin to signal EOF to subprocess
        if self._process.stdin:
            self._process.stdin.close()


async def main_async(args: Namespace) -> int:
    """Main async entry point."""
    # Set up signal handler for graceful shutdown
    loop = asyncio.get_running_loop()

    process: asyncio.subprocess.Process | None = None

    def signal_handler() -> None:
        """Handle SIGINT/SIGTERM by terminating the subprocess."""
        nonlocal process
        if process is not None and not process.done():
            process.cancel()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    # Initialize file logger if enabled
    file_logger: FileLogger | None = None
    if args.log_file:
        file_logger = FileLogger(Path(args.log_file))
        await file_logger.open()

    # Spawn subprocess first
    process = await asyncio.create_subprocess_exec(
        *args.command,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        # Create stream monitor with the spawned process
        monitor = StreamMonitor(
            process,
            stdin_json=args.stdin_json,
            stdout_json=args.stdout_json,
            stderr_json=args.stderr_json,
            expand_json=args.expand,
            file_logger=file_logger,
        )
        await monitor.run()
        return await process.wait()
    finally:
        # Cleanup
        if file_logger:
            await file_logger.close()


def main() -> int:
    """Main entry point - parses args and runs async main."""
    parser = ArgumentParser(
        prog="stream-spy",
        description="Intercept and monitor subprocess streams with JSON parsing.",
        epilog="Example: stream-spy --stdin-json --stdout-json uvx mcp-server-foo",
    )
    parser.add_argument(
        "command",
        nargs="+",
        help="Command and arguments to run as a subprocess",
    )
    parser.add_argument(
        "--stdin-json",
        action="store_true",
        help="Treat stdin input as JSON lines (with syntax highlighting)",
    )
    parser.add_argument(
        "--stdout-json",
        action="store_true",
        help="Treat stdout output as JSON lines (with syntax highlighting)",
    )
    parser.add_argument(
        "--stderr-json",
        action="store_true",
        help="Treat stderr output as JSON lines (with syntax highlighting)",
    )
    parser.add_argument(
        "--expand",
        action="store_true",
        help="Expand JSON objects to multi-line pretty print (default: compact single-line)",
    )
    parser.add_argument(
        "--log-file",
        type=str,
        help="Write all intercepted streams to a log file",
    )

    args = parser.parse_args()

    return asyncio.run(main_async(args))
