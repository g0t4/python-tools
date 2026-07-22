"""Public repair pipeline."""

from collections.abc import Iterable

from pyfmt.passes import IndentationRepairPass, RepairPass


class Repairer:
    """Apply independent repair passes in a deterministic order."""

    def __init__(self, passes: Iterable[RepairPass] | None = None) -> None:
        self._passes = tuple(passes or (IndentationRepairPass(),))

    def repair(self, source: str) -> str:
        lines = source.splitlines(keepends=True)
        for repair_pass in self._passes:
            lines = repair_pass.repair(lines)
        return "".join(lines)


def repair(source: str) -> str:
    """Repair *source* without applying any style formatting."""

    return Repairer().repair(source)
