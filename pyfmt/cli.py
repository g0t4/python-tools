"""Command-line interface for pyfmt."""

import argparse
from io import BytesIO
from pathlib import Path
import sys
import tokenize

from pyfmt.repair import repair


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pyfmt")
    subcommands = parser.add_subparsers(dest="command", required=True)
    repair_parser = subcommands.add_parser("repair", help="repair Python indentation")
    repair_parser.add_argument("file", type=Path)
    output = repair_parser.add_mutually_exclusive_group()
    output.add_argument(
        "--in-place", "-i", action="store_true", help="rewrite the input file"
    )
    output.add_argument(
        "--stdout", action="store_true", help="write repaired source to stdout (default)"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    original = args.file.read_bytes()
    encoding, _ = tokenize.detect_encoding(BytesIO(original).readline)
    source = original.decode(encoding)
    result = repair(source)
    if args.in_place:
        args.file.write_bytes(result.encode(encoding))
    else:
        sys.stdout.write(result)
    return 0
