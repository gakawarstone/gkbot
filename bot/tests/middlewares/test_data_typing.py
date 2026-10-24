"""Ensure incorrect uses of the project injection contract are rejected."""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = ROOT / "typing_tests" / "middleware_data"


@pytest.mark.parametrize("checker", ["mypy", "pyright"])
def test_middleware_data_contract(checker: str) -> None:
    source = FIXTURES / "invalid.py"
    command = [sys.executable, "-m", checker]
    if checker == "mypy":
        command += ["--follow-imports=silent", "--no-error-summary"]
    else:
        command += ["--outputjson", "--project", str(FIXTURES / "pyrightconfig.json")]
    command.append(str(source))
    result = subprocess.run(
        command,
        cwd=ROOT,
        env={**os.environ, "MYPYPATH": str(ROOT / "bot")},
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if checker == "mypy":
        errors = {
            int(line)
            for line in re.findall(r"invalid\.py:(\d+): error:", result.stdout)
        }
    else:
        report = json.loads(result.stdout)
        errors = {
            diagnostic["range"]["start"]["line"] + 1
            for diagnostic in report["generalDiagnostics"]
            if diagnostic["severity"] == "error"
        }
    expected = {
        number
        for number, line in enumerate(source.read_text().splitlines(), start=1)
        if "# error" in line
    }
    assert result.returncode == 1, result.stdout + result.stderr
    assert errors == expected, result.stdout + result.stderr
