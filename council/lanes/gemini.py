"""Gemini lane."""

from pathlib import Path

from .adapter import run as run_adapter


def run(prompt_file: Path, model: str) -> str:
    return run_adapter("gemini", prompt_file, model)
