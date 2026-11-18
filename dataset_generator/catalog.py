"""Names and paths for the complex, single-radar PRI benchmark (no model dependencies)."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
COMPLEX_DATASETS_ROOT = PROJECT_ROOT / "datasets" / "complex_pri_v1"
RADAR_TYPES = (
    "stable", "jitter", "stagger", "dwell_and_switch", "sliding",
    "sinusoidal", "triangular_sliding", "markov_agile",
)
ERROR_LEVELS = ("clean", *(f"error_lv{i}" for i in range(1, 8)))
STAGGER_ORDER = (
    0, 17, 5, 26, 11, 30, 3, 21, 14, 8, 28, 1, 19, 10, 24, 6,
    31, 15, 4, 23, 12, 27, 2, 18, 9, 29, 16, 7, 25, 13, 22, 20,
)


def sinusoidal_repeat_period(period: float) -> int:
    """Discrete period of the decimal N=p/q: p source samples in reduced form."""
    from fractions import Fraction

    return Fraction(str(float(period))).numerator


def check_dataset_selection(root: Path, profile: str, size: str,
                            radar_types=RADAR_TYPES, error_levels=ERROR_LEVELS) -> None:
    """Fail before model loading if a selected condition is missing; never generate data."""
    missing = [str(root / profile / kind / f"{size}_{level}")
               for kind in radar_types for level in error_levels
               if not (root / profile / kind / f"{size}_{level}" / "metadata.yaml").is_file()]
    if missing:
        raise FileNotFoundError("Missing selected datasets:\n" + "\n".join(missing))
