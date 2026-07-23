# pyfmt

`pyfmt` currently contains only the repair phase of a future Python formatter.
It makes conservative leading-indentation repairs without rewriting, joining,
or splitting source lines.

Preview a repair on stdout (the input file is not changed):

```console
uv run pyfmt repair path/to/file.py
```

Apply the repair in place:

```console
uv run pyfmt repair --in-place path/to/file.py
```

The indentation pass uses nearby Python block headers as evidence. It repairs
obvious over- and under-indentation, converts leading tabs to spaces, and leaves
continuation indentation and multiline string contents unchanged. A blank line
ends structural inference, so uncertain indentation is preserved.

Run the tests with:

```console
uv run pytest
```

## Terminology and references

The tooling and tests use Python's language-reference terminology where it is
helpful. These official references are useful when a term is unfamiliar:

### Chosen Terminology

We use **block** for the statements controlled by a compound-statement header,
especially when discussing formatting and repairs. CPython switched to its PEG
parser in Python 3.9, whose implementation grammar uses `block`; **suite** is
the traditional term retained by the language reference, and **body** describes
the statements owned by a particular AST node (such as a function or loop).
Unless discussing those specific grammar or AST representations, use **block**.

- [Full Python grammar](https://docs.python.org/3/reference/grammar.html) — the
  parser's rules for statements, compound statements, and their blocks (often
  called suites in Python discussions and older grammar terminology).
- [Lexical analysis](https://docs.python.org/3/reference/lexical_analysis.html)
  — physical and logical lines, comments, explicit and implicit line joining,
  indentation, blank lines, and source encodings.
- [`tokenize` standard-library module](https://docs.python.org/3/library/tokenize.html)
  — Python's token stream, including `INDENT`, `DEDENT`, comments, and encoding
  detection.
