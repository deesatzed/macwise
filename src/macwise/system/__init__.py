"""Safe host-system interfaces used by MacWise collectors."""

from macwise.system.commands import CommandResult, CommandState, ReadCommand, run_read_command

__all__ = ["CommandResult", "CommandState", "ReadCommand", "run_read_command"]
