"""Synthetic Radar PDW Data Generation Module."""

from .radar_generator import (
    Radar,
    StableRadar,
    JitterRadar,
    StaggerRadar,
    DwellAndSwitchRadar,
    SlidingRadar,
    Environment,
    apply_transmitter_clock_noise,
    apply_environmental_impacts,
)

__all__ = [
    "Radar",
    "StableRadar",
    "JitterRadar",
    "StaggerRadar",
    "DwellAndSwitchRadar",
    "SlidingRadar",
    "Environment",
    "apply_transmitter_clock_noise",
    "apply_environmental_impacts",
]

