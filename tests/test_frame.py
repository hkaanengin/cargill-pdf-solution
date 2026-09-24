"""The module surface exists and is reachable without Flask.

022 built the frame, not the behaviour, so what there is to assert is that the
five functions 0011 names are declared and that importing the module drags in
no web framework. The stubs that named the task owing each function are gone:
007 filled the last of them. The Flask check is the whole point of the split:
tests call the logic directly, with no browser and no HTTP.
"""

import subprocess
import sys
from pathlib import Path

import pytest

import stamper

SURFACE = ["route_filename", "load_workbook", "lookup_po", "stamp", "verify"]


def test_declares_the_whole_surface():
    missing = [name for name in SURFACE if not callable(getattr(stamper, name, None))]
    assert not missing, f"stamper.py is missing: {missing}"


def test_families_are_fatura_and_dekont():
    # Two families, because there are two sheets and two page layouts — R2-R4,
    # R12a. A third would mean the spec changed.
    assert {f.value for f in stamper.Family} == {"FATURA", "DEKONT"}


def test_imports_without_flask(repo_root: Path):
    """A subprocess, so a Flask import from anywhere else in the suite can't mask it."""
    probe = (
        "import sys; import stamper; "
        "sys.exit('flask reached stamper.py' if 'flask' in sys.modules else 0)"
    )
    done = subprocess.run(
        [sys.executable, "-c", probe], cwd=repo_root, capture_output=True, text=True
    )
    assert done.returncode == 0, done.stderr or done.stdout
