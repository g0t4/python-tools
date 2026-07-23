"""Repair passes.

The indentation pass deliberately uses a small lexical state machine.  Broken
indentation often makes ``ast`` and ``tokenize`` reject the input, precisely
when this tool needs to be useful.
"""

from dataclasses import dataclass
from typing import Protocol


class RepairPass(Protocol):
    """A single, independently testable source repair."""

    def repair(self, lines: list[str]) -> list[str]: ...


@dataclass(frozen=True)
class _LineInfo:
    code: str
    protected: bool
    continuation: bool


class _Scanner:
    """Identify structural code while ignoring strings and comments."""

    def __init__(self) -> None:
        self.quote: str | None = None
        self.bracket_depth = 0
        self.explicit_continuation = False

    def scan(self, text: str) -> _LineInfo:
        depth_before = self.bracket_depth
        continuation = depth_before > 0 or self.explicit_continuation
        protected = self.quote is not None
        code: list[str] = []
        index = 0

        while index < len(text):
            if self.quote is not None:
                end = text.find(self.quote, index)
                if end < 0:
                    index = len(text)
                    continue
                index = end + len(self.quote)
                self.quote = None
                continue

            char = text[index]
            if char == "#":
                break
            if char in "'\"":
                triple = char * 3
                if text.startswith(triple, index):
                    end = text.find(triple, index + 3)
                    if end < 0:
                        self.quote = triple
                        index = len(text)
                    else:
                        index = end + 3
                    continue
                index = self._skip_short_string(text, index, char)
                continue
            if char in "([{":
                self.bracket_depth += 1
            elif char in ")]}" and self.bracket_depth:
                self.bracket_depth -= 1
            code.append(char)
            index += 1

        stripped = "".join(code).rstrip()
        self.explicit_continuation = bool(stripped.endswith("\\"))
        return _LineInfo(stripped.strip(), protected, continuation)

    @staticmethod
    def _skip_short_string(text: str, index: int, quote: str) -> int:
        index += 1
        escaped = False
        while index < len(text):
            char = text[index]
            index += 1
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                break
        return index


class IndentationRepairPass:
    """Repair indentation only where nearby block structure makes it clear.

    A blank line is treated as an inference boundary.  This is intentionally
    conservative: later passes can grow smarter without making this pass
    silently reinterpret distant code.
    """

    INDENT = 4
    _CLAUSES = ("elif ", "else:", "except", "finally:", "case ")
    _TOP_LEVEL_BOUNDARIES = ("def ", "async def ", "class ", "@")

    def repair(self, lines: list[str]) -> list[str]:
        scanner = _Scanner()
        repaired: list[str] = []
        blocks: list[tuple[int, bool]] = []
        previous_indent: int | None = None
        previous_opened_block = False

        for line in lines:
            line_text, ending = self._split_ending(line)
            expanded = line_text.expandtabs(self.INDENT)
            content = expanded.lstrip(" ")
            info = scanner.scan(content)

            if not content:
                repaired.append(line_text + ending)
                blocks.clear()
                previous_indent = None
                previous_opened_block = False
                continue

            raw_indent = len(expanded) - len(content)
            if info.protected or info.continuation or not info.code:
                repaired.append(expanded + ending)
                comment_is_first_line_of_block = (
                    content.startswith("#")
                    and previous_opened_block
                    and previous_indent is not None
                    and raw_indent == previous_indent + self.INDENT
                )
                if (
                    content.startswith("#")
                    and not info.protected
                    and not info.continuation
                    and not comment_is_first_line_of_block
                ):
                    # A comment-only line is a visual block boundary for
                    # under-indentation inference. Keep ``previous_indent`` so
                    # it can still anchor a clear over-indentation repair. A
                    # correctly indented comment immediately beneath a block
                    # header is part of that block, rather than a separator.
                    blocks.clear()
                    previous_opened_block = False
                continue

            indent = raw_indent
            top_level_boundary = raw_indent == 0 and info.code.startswith(
                self._TOP_LEVEL_BOUNDARIES
            )

            if previous_opened_block and previous_indent is not None:
                indent = previous_indent + self.INDENT
            elif self._is_clause(info.code) and blocks:
                header_indent, header_is_case = blocks[-1]
                indent = header_indent
                if info.code.startswith("case ") and not header_is_case:
                    indent += self.INDENT
                blocks.pop()
            else:
                valid_block_indents = {
                    header_indent + self.INDENT for header_indent, _ in blocks
                }
                if raw_indent in valid_block_indents:
                    indent = raw_indent
                    while blocks and blocks[-1][0] >= indent:
                        blocks.pop()
                elif (
                    blocks
                    and raw_indent < blocks[0][0] + self.INDENT
                    and not top_level_boundary
                ):
                    indent = blocks[0][0] + self.INDENT
                elif previous_indent is not None and raw_indent > previous_indent:
                    indent = previous_indent

            repaired.append(" " * indent + content + ending)
            previous_indent = indent
            previous_opened_block = self._opens_block(info.code)
            if previous_opened_block:
                blocks.append((indent, info.code.startswith("case ")))

        return repaired

    @staticmethod
    def _split_ending(line: str) -> tuple[str, str]:
        if line.endswith("\r\n"):
            return line[:-2], "\r\n"
        if line.endswith(("\n", "\r")):
            return line[:-1], line[-1]
        return line, ""

    @staticmethod
    def _opens_block(code: str) -> bool:
        return code.endswith(":")

    def _is_clause(self, code: str) -> bool:
        return code.startswith(self._CLAUSES)
