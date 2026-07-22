
import pytest

from pyfmt import repair


def test_simple_overindent():
    before = """
def foo():
    x = 1
        y = 2
"""

    after = """
def foo():
    x = 1
    y = 2
"""

    assert repair(before) == after


@pytest.mark.parametrize(
    ("before", "after"),
    [
        ("def foo():\nx = 1\n", "def foo():\n    x = 1\n"),
        (
            "def foo():\n    if ready:\nvalue = 1\n",
            "def foo():\n    if ready:\n        value = 1\n",
        ),
        (
            "def foo():\n    if ready:\n        yes()\n    no()\n",
            "def foo():\n    if ready:\n        yes()\n    no()\n",
        ),
        (
            "def foo():\n    for item in items:\n            use(item)\n",
            "def foo():\n    for item in items:\n        use(item)\n",
        ),
    ],
)
def test_repairs_clear_suite_indentation(before: str, after: str) -> None:
    assert repair(before) == after


def test_blank_line_ends_conservative_inference() -> None:
    source = "def foo():\n    work()\n\nnot_known = 1\n"
    assert repair(source) == source


def test_comment_group_separator_stops_underindent_inference() -> None:
    source = (
        "async def handle(connection, keystroke):\n"
        "    e = keystroke.keycode == iterm2.Keycode.ANSI_MINUS\n"
        "    if e and control and shift and command:\n"
        "        await smaller_font_wes_stops(connection)\n"
        "        return\n"
        "    #\n"
        "e = keystroke.keycode == iterm2.Keycode.ANSI_EQUAL\n"
        "if e and control and shift and command:\n"
        "    await bigger_font_wes_stops(connection)\n"
        "    return\n"
    )

    assert repair(source) == source


def test_comment_group_separator_does_not_disable_overindent_repair() -> None:
    before = "def foo():\n    first = 1\n    # next group\n        second = 2\n"
    after = "def foo():\n    first = 1\n    # next group\n    second = 2\n"
    assert repair(before) == after


def test_comment_as_first_line_of_if_body_preserves_suite_indentation() -> None:
    source = (
        "async def handle(connection, keystroke):\n"
        "    e = keystroke.keycode == iterm2.Keycode.ANSI_F\n"
        "    if e and control and shift and command:\n"
        "        # TODO merge with ANSI_B?\n"
        "        await copy_screen_to_clipboard(connection, history=False)\n"
        "        return\n"
    )

    assert repair(source) == source


def test_new_top_level_definition_is_a_boundary_without_blank_line() -> None:
    source = "def one():\n    pass\ndef two():\n    pass\n"
    assert repair(source) == source


def test_preserves_continuation_indentation_and_multiline_string_contents() -> None:
    source = (
        "def foo():\n"
        "    values = [\n"
        "             1,\n"
        "      2,\n"
        "    ]\n"
        "    text = \"\"\"first\n"
        "          literal indentation\n"
        "    last\"\"\"\n"
    )
    assert repair(source) == source


def test_normalizes_leading_tabs_to_four_space_stops() -> None:
    assert repair("def foo():\n\treturn 1\n") == "def foo():\n    return 1\n"


@pytest.mark.parametrize(
    "source",
    [
        (
            "def foo():\n"
            "    try:\n"
            "        work()\n"
            "    except ValueError:\n"
            "        recover()\n"
            "    finally:\n"
            "        clean_up()\n"
        ),
        (
            "def foo(value):\n"
            "    match value:\n"
            "        case 1:\n"
            "            one()\n"
            "        case _:\n"
            "            other()\n"
        ),
        (
            "def foo():\n"
            "    if ready:\n"
            "        yes()\n"
            "    else:\n"
            "        no()\n"
        ),
    ],
)
def test_preserves_valid_compound_statements(source: str) -> None:
    assert repair(source) == source


def test_preserves_whitespace_on_blank_lines() -> None:
    source = "def foo():\n    pass\n \t \nvalue = 1\n"
    assert repair(source) == source


def test_is_idempotent() -> None:
    source = "def foo():\n        if ready:\nvalue = 1\n"
    once = repair(source)
    assert repair(once) == once
