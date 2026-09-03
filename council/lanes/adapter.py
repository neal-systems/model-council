"""The one adapter boundary between the council and a model provider."""

from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path

from .fake import run as run_fake


def run(vendor: str, prompt_file: Path, model: str) -> str:
    """Return model text for one prompt file.

    If ``COUNCIL_<VENDOR>_COMMAND`` is unset, use the offline fake.  A real
    command receives ``--prompt-file PATH --model MODEL`` and must print the
    model response on stdout.
    """

    command = os.environ.get(f"COUNCIL_{vendor.upper()}_COMMAND")
    if not command:
        return run_fake(prompt_file, model, vendor)
    argv = [*shlex.split(command), "--prompt-file", str(prompt_file), "--model", model]
    completed = subprocess.run(argv, capture_output=True, text=True, timeout=300)
    if completed.returncode != 0:
        detail = completed.stderr.strip() or f"exit {completed.returncode}"
        raise RuntimeError(f"{vendor} lane failed: {detail}")
    if not completed.stdout.strip():
        raise RuntimeError(f"{vendor} lane returned no text")
    return completed.stdout.strip()
