"""Vendor lane adapters.

Each module exports ``run(prompt_file, model) -> str``.  With no command
configured, the adapters call the deterministic fake lane.
"""

from . import claude, codex, gemini

LANES = {"claude": claude.run, "codex": codex.run, "gemini": gemini.run}

__all__ = ["LANES"]
