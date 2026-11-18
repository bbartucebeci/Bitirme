"""Checks for read-only gallery windows, including 1025-row captures."""
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from dataset_generator.plot_sequence_gallery import load_sequence


class GalleryWindowTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / "seq.csv"

    def write_capture(self, intervals):
        pd.DataFrame({
            "Radar_ID": "R_SINGLE", "pulse_index": np.arange(intervals+1),
            "Measured_Delta_TOA": np.r_[0., np.full(intervals, 1000.)],
            "PRI": 1000., "Frequency": 9000., "PW": 1.5,
            "Amplitude": -55., "AOA": 45.,
        }).to_csv(self.path, index=False)

    def test_anchor_removed_for_both_capture_lengths_without_writes(self):
        for intervals in (128, 1024):
            self.write_capture(intervals)
            before = self.path.read_bytes()
            frame = load_sequence(self.path, intervals)
            self.assertEqual(len(frame), intervals)
            self.assertEqual(frame.pulse_index.iloc[0], 1)
            self.assertEqual(frame.pulse_index.iloc[-1], intervals)
            self.assertEqual(before, self.path.read_bytes())

    def test_window_start_is_after_anchor(self):
        self.write_capture(1024)
        frame = load_sequence(self.path, 20, start=10)
        np.testing.assert_array_equal(frame.pulse_index, np.arange(11, 31))

    def test_short_window_is_rejected(self):
        self.write_capture(1024)
        with self.assertRaisesRegex(ValueError, "only 1024 intervals"):
            load_sequence(self.path, 1025)


if __name__ == "__main__":
    unittest.main()
