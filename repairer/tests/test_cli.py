from pathlib import Path

from pyfmt.cli import main


def test_cli_prints_to_stdout_by_default(tmp_path: Path, capsys) -> None:
    path = tmp_path / "broken.py"
    original = "def foo():\n        value = 1\n"
    path.write_text(original)

    assert main(["repair", str(path)]) == 0

    assert capsys.readouterr().out == "def foo():\n    value = 1\n"
    assert path.read_text() == original


def test_cli_can_rewrite_in_place(tmp_path: Path, capsys) -> None:
    path = tmp_path / "broken.py"
    path.write_text("def foo():\nvalue = 1\n")

    assert main(["repair", "--in-place", str(path)]) == 0

    assert capsys.readouterr().out == ""
    assert path.read_text() == "def foo():\n    value = 1\n"


def test_cli_preserves_crlf_and_declared_encoding(tmp_path: Path) -> None:
    path = tmp_path / "broken.py"
    original = "# coding: latin-1\r\ndef café():\r\nreturn 1\r\n".encode("latin-1")
    path.write_bytes(original)

    assert main(["repair", "--in-place", str(path)]) == 0

    assert path.read_bytes() == (
        "# coding: latin-1\r\ndef café():\r\n    return 1\r\n".encode("latin-1")
    )
