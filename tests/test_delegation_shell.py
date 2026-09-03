import subprocess
from pathlib import Path


def test_delegation_shell_suite():
    root = Path(__file__).resolve().parents[1]
    completed = subprocess.run(["bash", "delegation/tests/run.sh"], cwd=root, capture_output=True, text=True)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "9 shell checks passed" in completed.stdout
