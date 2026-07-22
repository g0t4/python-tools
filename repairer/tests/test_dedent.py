
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
