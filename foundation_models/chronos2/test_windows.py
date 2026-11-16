"""Checks that Chronos and classical methods evaluate the same pulse windows."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from classic_methods.common import draw_window_start
from foundation_models.common.windowing import WINDOW_SEED, file_sha256, load_test_manifest, window_key
from foundation_models.common.dataset import load_split
from foundation_models.common.metrics import score_single


class WindowProtocolTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dataset_dir = Path(self.tmp.name) / "fixed" / "stable" / "1000x1024_clean"
        metadata = {
            "profile_mode": "fixed", "radar_type": "stable", "error_level": "clean",
            "sequence_count": 3, "expected_pulses_per_sequence": 1024,
            "split": {s: {"sequence_count": 1} for s in ("train", "val", "test")},
        }
        self.dataset_dir.mkdir(parents=True)
        (self.dataset_dir / "metadata.yaml").write_text(yaml.safe_dump(metadata), encoding="utf-8")
        for split, sid in (("train", "seq_0000"), ("val", "seq_0001"), ("test", "seq_0002")):
            folder = self.dataset_dir / split
            folder.mkdir()
            intervals = np.arange(1024, dtype=np.float32)
            frame = pd.DataFrame({
                "sequence_id": sid,
                "pulse_index": np.arange(1025),
                "Radar_ID": "R_SINGLE",
                "Measured_Delta_TOA": np.r_[0.0, intervals + 100.0],
                "PRI": np.r_[-1.0, intervals],
                "Frequency": 9000.0,
                "PW": 1.0,
                "AOA": 25.0,
                "Amplitude": -30.0,
            })
            frame.to_csv(folder / f"{sid}.csv", index=False)

    def test_random_test_windows_match_classical_manifest(self) -> None:
        for length in (96, 256, 512, 992):
            key = window_key("fixed", "stable", "clean", "seq_0002", length)
            start = draw_window_start(1024, length, 32, WINDOW_SEED, key)
            manifest = {
                "meta": {"split": "test", "window_mode": "random", "dataset_size": "1000x1024", "horizon_len": 32,
                         "context_lens": [length], "seed": WINDOW_SEED},
                "sequence_lengths": {"fixed/stable/clean/seq_0002": 1024},
                "sequence_sha256": {"fixed/stable/clean/seq_0002":
                                    file_sha256(self.dataset_dir / "test" / "seq_0002.csv")},
                "windows": {key: start},
            }
            loaded = load_split(self.dataset_dir, "test", "PRI", length, 32,
                                window_mode="random", window_manifest=manifest)
            window = loaded.windows[0]
            self.assertEqual(window.start, start)
            np.testing.assert_array_equal(window.context[0], np.arange(start + 100, start + length + 100))
            np.testing.assert_array_equal(window.target[0], np.arange(start + length, start + length + 32))
            self.assertTrue(window.emitter_mask.all())
            self.assertTrue(window.context.flags.writeable)
            self.assertTrue(window.target.flags.writeable)
            if length == 992:
                self.assertEqual(start, 0)

    def test_split_draws_are_reproducible_and_test_requires_manifest(self) -> None:
        a = load_split(self.dataset_dir, "train", context_len=256, window_mode="random")
        b = load_split(self.dataset_dir, "train", context_len=256, window_mode="random")
        self.assertEqual(a.windows[0].start, b.windows[0].start)
        with self.assertRaisesRegex(ValueError, "test manifest"):
            load_split(self.dataset_dir, "test", window_mode="random")

    def test_tail_windows_share_exact_targets(self) -> None:
        for length in (96, 256, 512, 992):
            window = load_split(self.dataset_dir, "test", context_len=length,
                                window_mode="tail").windows[0]
            self.assertEqual(window.start, 992 - length)
            np.testing.assert_array_equal(window.target[0], np.arange(992, 1024))

    def test_invalid_start_and_unscorable_target_are_rejected(self) -> None:
        key = window_key("fixed", "stable", "clean", "seq_0002", 992)
        manifest = {"sequence_lengths": {"fixed/stable/clean/seq_0002": 1024},
                    "sequence_sha256": {"fixed/stable/clean/seq_0002":
                                        file_sha256(self.dataset_dir / "test" / "seq_0002.csv")},
                    "windows": {key: 1}}
        with self.assertRaisesRegex(ValueError, "outside"):
            load_split(self.dataset_dir, "test", context_len=992,
                       window_mode="random", window_manifest=manifest)
        self.assertIsNone(score_single(np.ones(32), np.zeros(32),
                                       np.zeros(32, dtype=bool), "PRI", unrounded=True))
        tiny = score_single(np.full(32, 0.0001), np.zeros(32), np.ones(32, dtype=bool),
                            "PRI", unrounded=True)
        self.assertGreater(tiny["mae"], 0)

    def test_manifest_metadata_and_sequence_length_are_checked(self) -> None:
        path = Path(self.tmp.name) / "windows.json"
        key = window_key("fixed", "stable", "clean", "seq_0002", 96)
        manifest = {"meta": {"split": "test", "window_mode": "random", "dataset_size": "1000x1024", "horizon_len": 32,
                             "context_lens": [96], "seed": WINDOW_SEED},
                    "sequence_lengths": {"fixed/stable/clean/seq_0002": 1023},
                    "sequence_sha256": {"fixed/stable/clean/seq_0002":
                                        file_sha256(self.dataset_dir / "test" / "seq_0002.csv")},
                    "windows": {key: 0}}
        path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "manifest seed"):
            load_test_manifest(path, "1000x1024", 96, 32, WINDOW_SEED + 1)
        loaded = load_test_manifest(path, "1000x1024", 96, 32, WINDOW_SEED)
        with self.assertRaisesRegex(ValueError, "sequence length"):
            load_split(self.dataset_dir, "test", context_len=96,
                       window_mode="random", window_manifest=loaded)
        loaded["sequence_lengths"]["fixed/stable/clean/seq_0002"] = 1024
        loaded["sequence_sha256"]["fixed/stable/clean/seq_0002"] = "wrong"
        with self.assertRaisesRegex(ValueError, "differs from the window manifest"):
            load_split(self.dataset_dir, "test", context_len=96,
                       window_mode="random", window_manifest=loaded)


if __name__ == "__main__":
    unittest.main()
