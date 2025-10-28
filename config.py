"""Application-wide configuration helpers and constants."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

BASE_DIR: Path = Path(__file__).resolve().parent
DATA_SUBDIRECTORIES = ("data", ".")


def resolve_data_path(filename: str) -> Path:
    """Return the first existing path for the given filename.

    Preference order: ``data/`` directory, then project root. Raises ``FileNotFoundError``
    with a helpful message if the file cannot be located anywhere.
    """

    for relative_dir in DATA_SUBDIRECTORIES:
        candidate = (BASE_DIR / relative_dir).joinpath(filename)
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        f"Unable to locate '{filename}'. Expected to find it in one of: "
        f"{[str((BASE_DIR / rel_dir).resolve()) for rel_dir in DATA_SUBDIRECTORIES]}"
    )


def optional_data_path(filename: str) -> Optional[Path]:
    """Gracefully resolve a data path; return ``None`` if not found."""

    try:
        return resolve_data_path(filename)
    except FileNotFoundError:
        return None


# Model configuration -----------------------------------------------------------------
DEFAULT_TOP_N = 10
SIMILARITY_WEIGHT = 0.75  # Weight assigned to textual similarity vs. popularity
N_NEIGHBORS = 30  # Retrieve a slightly larger candidate pool and re-rank manually
TFIDF_MAX_FEATURES = 20000
TFIDF_NGRAM_RANGE = (1, 2)
TFIDF_MIN_DF = 2
