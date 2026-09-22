"""Fixtures over the real data: the workbook, and the ten sample PDFs.

Every test reaches its data through a fixture here. Nothing hardcodes a path,
so the workbook being replaced — it already has been once — is a one-line
change in this file rather than a sweep through the suite.

The data these point at is described in `vault/architecture/data-layout.md`.

`samples_stamped_reference/` is deliberately **not** exposed as an input
fixture. Those six files are stamp-placement evidence, and feeding one to the
app is precisely the already-stamped exception in R18
(`vault/decisions/0010-destamped-sample-pdfs.md`). When 007 comes to test that
refusal it will want them — as the thing being refused, under a name that says
so, not as an input the suite can reach for by accident.
"""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

# The workbook is uploaded per session in the app (R24); for the suite it is
# the copy in the repo.
WORKBOOK_NAME = "SUBASI FATURA-DEKONT AGUSTOS.xlsx"
SAMPLES_DIR_NAME = "sgm_folders"


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def workbook_path(repo_root: Path) -> Path:
    """The real workbook, as a path."""
    path = repo_root / WORKBOOK_NAME
    if not path.is_file():
        pytest.fail(
            f"Workbook fixture missing: {path}. A new workbook replaces the old "
            f"one under the same name — update WORKBOOK_NAME in tests/conftest.py "
            f"if that has changed."
        )
    return path


@pytest.fixture(scope="session")
def samples_dir(repo_root: Path) -> Path:
    path = repo_root / SAMPLES_DIR_NAME
    if not path.is_dir():
        pytest.fail(f"Sample directory missing: {path}")
    return path


@pytest.fixture(scope="session")
def sample_pdfs(samples_dir: Path) -> dict[str, Path]:
    """Every sample PDF, keyed by its stem — which is also its lookup key (R1).

    Discovered rather than listed, so a sample added to the directory is
    available without editing this file.
    """
    found = {p.stem: p for p in sorted(samples_dir.glob("*.pdf"))}
    if not found:
        pytest.fail(f"No sample PDFs in {samples_dir}")
    return found


@pytest.fixture(scope="session")
def sample_path(sample_pdfs: dict[str, Path]):
    """`sample_path("917031")` -> Path. Fails loudly on a name that is not there."""

    def _get(stem: str) -> Path:
        if stem not in sample_pdfs:
            pytest.fail(
                f"No sample named {stem!r}. Available: {sorted(sample_pdfs)}"
            )
        return sample_pdfs[stem]

    return _get


@pytest.fixture(scope="session")
def sample_bytes(sample_path):
    """`sample_bytes("917031")` -> bytes, which is what `stamp()` takes."""

    def _read(stem: str) -> bytes:
        return sample_path(stem).read_bytes()

    return _read
