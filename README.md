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

The indentation pass uses nearby Python suite headers as evidence. It repairs
obvious over- and under-indentation, converts leading tabs to spaces, and leaves
continuation indentation and multiline string contents unchanged. A blank line
ends structural inference, so uncertain indentation is preserved.

Run the tests with:

```console
uv run pytest
```
