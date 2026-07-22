Create a new Python project named `pyfmt`.

The project should be architected around two completely separate phases:

1. Repairer
2. Formatter

The Repairer is responsible for making Python source structurally sane with the smallest possible changes. The Formatter is responsible for style normalization.

For the initial implementation, only implement the Repairer.

## Architecture

- Python 3.12+
- Fully typed.
- pytest for tests, TDD this as much as possible the tests are how wes can communicate clearly with you!
- Clean, modular architecture.
- Easy to add additional repair passes later.

## Initial Repairer behavior:

- Read a Python source file.
- Preserve all existing line breaks.
- Preserve comments.
- Preserve the order of statements.
- Never rewrite expressions.
- Never join lines.
- Never split lines.
- Only modify leading indentation when appropriate.

Implement the Repairer as a pipeline of independent repair passes:

    RepairPass
        repair(lines) -> lines

The initial pass should be IndentationRepairPass.

IndentationRepairPass should:

- Normalize indentation using spaces only.
- Remove clearly excessive indentation.
- Never increase indentation during the initial proof of concept.
- Be conservative.
- Favor leaving questionable code unchanged over making risky modifications.
- Be deterministic and idempotent.

Design the architecture so future repair passes can easily be added, for example:

- ContinuationIndentRepairPass
- TabsRepairPass
- BlankLineRepairPass
- TrailingWhitespaceRepairPass

Create a CLI:

    pyfmt repair file.py

which rewrites the file in place.

Include a comprehensive pytest suite.

The implementation should prioritize readability over cleverness.

Avoid regex-heavy code when a simple state machine or tokenizer is clearer.

Do not implement formatting yet. Only build the repair framework and the indentation repair pass.
