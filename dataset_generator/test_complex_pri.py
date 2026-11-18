"""Source-law and dataset integration checks; no model downloads or full datasets."""
import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

from dataset_generator.generate_datasets import (
    CONFIGS_DIR, RADAR_CLASSES, RADAR_TYPES, ERROR_LEVELS, build_single_dataset,
    generate_single_radar_sequence, get_fixed_profile, load_all_configs,
    sample_common_profile, sample_radar_profile, validate_profile,
)
from dataset_generator.catalog import STAGGER_ORDER, sinusoidal_repeat_period


class ComplexPRITest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.errors, cls.profiles, _ = load_all_configs(CONFIGS_DIR)

    def radar(self, kind, **overrides):
        args = get_fixed_profile(kind, self.profiles["fixed_profiles"])["pri_args"]
        return RADAR_CLASSES[kind](radar_id="R_SINGLE", freq_mean=9000, **args, **overrides)

    def test_fixed_definitions_and_source_cycles(self):
        stagger = self.radar("stagger").source_pris(64)
        expected = np.linspace(750, 1250, 32)[list(STAGGER_ORDER)]
        np.testing.assert_array_equal(stagger[:32], expected)
        np.testing.assert_array_equal(stagger[:32], stagger[32:])
        self.assertAlmostEqual(stagger.mean(), 1000)
        dwell = self.radar("dwell_and_switch").source_pris(320)
        expected = np.repeat([850, 1075, 925, 1150, 1000], 32)
        np.testing.assert_array_equal(dwell[:160], expected)
        np.testing.assert_array_equal(dwell[160:], expected)
        self.assertAlmostEqual(dwell.mean(), 1000)

    def test_triangle_has_ten_up_ten_down_without_duplicate_turns(self):
        values = self.radar("triangular_sliding").source_pris(40)
        expected = np.r_[np.arange(850, 1150, 30), np.arange(1150, 850, -30)]
        np.testing.assert_array_equal(values[:20], expected)
        np.testing.assert_array_equal(values[:20], values[20:])
        delta = np.diff(np.r_[values[:20], values[0]])
        self.assertEqual((delta == 30).sum(), 10)
        self.assertEqual((delta == -30).sum(), 10)
        self.assertAlmostEqual(values.mean(), 1000)

    def test_sinusoidal_formula_and_noninteger_repeat(self):
        radar = self.radar("sinusoidal", phase_rad=1.2)
        values = radar.source_pris(2048)
        np.testing.assert_allclose(values, 1000 + 150*np.sin(2*np.pi*np.arange(2048)/7.2391+1.2))
        self.assertEqual(sinusoidal_repeat_period(7.2391), 72391)
        for shift in range(1, 1025):
            self.assertFalse(np.allclose(values[:512], values[shift:shift+512], rtol=0, atol=1e-8))

    def test_markov_transitions_and_capture_prefix(self):
        radar = self.radar("markov_agile", initial_state=3, source_seed=1701)
        values = radar.source_pris(200000)
        np.testing.assert_array_equal(values[:100], radar.source_pris(100))
        np.testing.assert_array_equal(radar.levels, [850,950,1050,1150])
        state = np.searchsorted(radar.levels, values)
        self.assertEqual(state[0], 3)
        for current in range(4):
            successors = state[1:][state[:-1] == current]
            for successor in range(4):
                expected = .7 if successor == (current+1)%4 else .1
                self.assertEqual(radar.transition_matrix[current,successor], expected)
                self.assertAlmostEqual(float(np.mean(successors==successor)), expected, delta=.007)
            self.assertAlmostEqual(float(np.mean(state==current)), .25, delta=.01)
        self.assertAlmostEqual(float(values.mean()), 1000, delta=5)

    def test_phases_and_existing_zero_phase_behavior(self):
        for kind, cycle in (("stagger",32),("dwell_and_switch",160),("sliding",16),("triangular_sliding",20)):
            base = self.radar(kind).source_pris(cycle)
            shifted = self.radar(kind,pattern_phase=7).source_pris(cycle)
            np.testing.assert_array_equal(shifted, np.roll(base,-7))
        np.testing.assert_allclose(self.radar("sliding").source_pris(16),np.linspace(850,1150,16))

    def test_varying_ranges_and_expected_means(self):
        sampling = self.profiles["varying_profile_sampling"]
        counts, dwells = set(), set()
        for kind in RADAR_TYPES:
            rng = np.random.default_rng(20261020)
            for i in range(1000):
                common = sample_common_profile(rng,str(i),sampling)
                p = sample_radar_profile(kind,common,rng,sampling)
                validate_profile(kind,p)
                for key,lo,hi in (("mean_pri_us",800,1200),("freq_mean_mhz",8900,9100),
                                  ("pw_mean_us",1,2),("amp_mean_dbm",-65,-45),("aoa_mean_deg",0,360)):
                    self.assertTrue(lo <= p[key] <= hi)
                self.assertEqual(p["freq_mode"],"constant")
                args = p["pri_args"]
                if kind == "stagger":
                    counts.add(p["level_count"])
                    self.assertTrue(.24 <= p["span_fraction"] <= .30)
                    self.assertGreater(np.min(np.diff(np.sort(args["stagger_pris"]))),10)
                    self.assertEqual(sorted(p["level_order"]),list(range(p["level_count"])))
                    self.assertAlmostEqual(np.mean(args["stagger_pris"]),p["mean_pri_us"])
                if kind == "dwell_and_switch":
                    dwells.add(args["pulses_per_dwell"])
                    self.assertAlmostEqual(np.mean(args["dwell_pris"]),p["mean_pri_us"])
                if kind == "sinusoidal":
                    self.assertTrue(6.5 <= args["period"] <= 9.5)
                    self.assertGreater(sinusoidal_repeat_period(args["period"]),1024)
                if kind == "markov_agile":
                    s = p["span_fraction"]
                    np.testing.assert_allclose(args["pri_levels"],p["mean_pri_us"]*np.array([1-s,1-s/3,1+s/3,1+s]))
                    self.assertAlmostEqual(np.mean(args["pri_levels"]),p["mean_pri_us"])
                    np.testing.assert_array_equal(args["transition_matrix"],self.profiles["fixed_profiles"]["markov_agile"]["transition_matrix"])
        self.assertEqual(counts,set(range(16,33)))
        self.assertEqual(dwells,{32,48,64})

    def test_stagger_gap_boundaries_and_strict_ten_us_rejection(self):
        fixed = get_fixed_profile("stagger",self.profiles["fixed_profiles"])
        fixed_gap = np.min(np.diff(np.sort(fixed["pri_args"]["stagger_pris"])))
        self.assertAlmostEqual(fixed_gap,500/31)
        for mean in (800.,1200.):
            for span in (.24,.30):
                for count in (16,32):
                    profile=copy.deepcopy(fixed)
                    profile["mean_pri_us"]=mean
                    levels=np.linspace(mean*(1-span),mean*(1+span),count)
                    profile["pri_args"]["stagger_pris"]=levels.tolist()
                    validate_profile("stagger",profile)
                    self.assertGreater(np.min(np.diff(levels)),10)
                    self.assertGreaterEqual(np.min(np.diff(levels)),2*800*.24/31-1e-9)
        for gap in (10.,9.9):
            profile=copy.deepcopy(fixed)
            profile["pri_args"]["stagger_pris"]=(1000+gap*(np.arange(32)-15.5)).tolist()
            with self.assertRaisesRegex(ValueError,"more than 10"):
                validate_profile("stagger",profile)

    def test_error_table(self):
        self.assertEqual(tuple(self.errors),ERROR_LEVELS)
        for i,poi in enumerate((1,.995,.99,.98,1,.95,.85,.75)):
            key = ERROR_LEVELS[i]
            self.assertEqual(self.errors[key]["poi"],poi)
            self.assertEqual(self.errors[key]["noise_rate"],0)
            self.assertEqual(self.errors[key]["multipath_prob"],0)
        for key in ERROR_LEVELS[4:]:
            for parameter in self.errors["error_lv2"]:
                if parameter != "poi":
                    self.assertEqual(self.errors[key][parameter],self.errors["error_lv2"][parameter])

    def test_losses_keep_source_index_and_expected_rates(self):
        # Isolate losses from clock/noise. Observed gaps must sum skipped source PRIs.
        radar = self.radar("stagger")
        radar.poi=.75
        for attr in ("clock_bias","clock_offset","clock_drift","jitter_k","jitter_std"):
            setattr(radar,attr,0)
        from synthetic_data_generation.radar_generator import Environment
        env=Environment(); env.add_radar(radar)
        np.random.seed(123)
        df=env.generate(duration=100_000_000,pw_noise_std=0,amp_noise_std=0,aoa_noise_std=0,global_drop_rate=.005)
        pattern=radar.source_pris(101000)
        times=np.cumsum(pattern)-pattern[0]
        # Locate first source event by modulo cycle time, then recover every source index.
        # Capture offset is one uniform(0,2000) draw, independent of source losses.
        np.random.seed(123); offset=float(np.random.uniform(0,2000))
        idx=np.searchsorted(times,df.TOA.to_numpy()-offset-1e-6)
        np.testing.assert_allclose(df.PRI.to_numpy(),pattern[idx],atol=1e-7)
        np.testing.assert_allclose(df.Measured_Delta_TOA.to_numpy()[1:],np.diff(times[idx]),atol=1e-7)
        source_count=int(np.searchsorted(times,100_000_000,side="right"))
        self.assertAlmostEqual(len(df)/source_count,.75*.995,delta=.006)
        self.assertTrue((np.diff(idx)>1).any())

    def test_sequence_length_reproducibility_and_retries(self):
        for kind in RADAR_TYPES:
            profile=get_fixed_profile(kind,self.profiles["fixed_profiles"])
            outputs=[]
            for _ in range(2):
                np.random.seed(88)
                outputs.append(generate_single_radar_sequence(kind,profile,self.errors["error_lv7"],"seq","error_lv7",1024))
            pd.testing.assert_frame_equal(*outputs)
            df=outputs[0]
            self.assertEqual(len(df),1025)
            self.assertEqual(set(df.Radar_ID),{"R_SINGLE"})
            self.assertEqual(df.Measured_Delta_TOA.iloc[0],0)
            self.assertTrue((np.diff(df.TOA)>0).all())
        profile=get_fixed_profile("dwell_and_switch",self.profiles["fixed_profiles"])
        from dataset_generator import generate_datasets as module
        original=module.Environment.generate
        phases=[]
        def short_first(env,*args,**kwargs):
            phases.append(env.radars[0].pattern_phase)
            result=original(env,*args,**kwargs)
            return result.iloc[:3] if len(phases)==1 else result
        with patch.object(module.Environment,"generate",short_first):
            generate_single_radar_sequence("dwell_and_switch",profile,self.errors["clean"],"retry","clean",1024)
        self.assertEqual(len(phases),2)
        self.assertEqual(phases[0],phases[1])

    def test_writer_splits_and_overwrite_protection(self):
        with tempfile.TemporaryDirectory() as directory:
            kwargs=dict(output_root=Path(directory),radar_type="markov_agile",profile_mode="fixed",error_level="clean",
                        sequence_count=10,pulses_per_sequence=1024,seed=123,error_config=self.errors["clean"],profiles_cfg=self.profiles)
            build_single_dataset(**kwargs)
            folder=Path(directory)/"single_radar/fixed/markov_agile/10x1024_clean"
            for name,count in (("train",7),("val",1),("test",2)):
                self.assertEqual(len(list((folder/name).glob("seq_*.csv"))),count)
                self.assertEqual(len(pd.read_csv(folder/name/"sequences.csv")),count*1025)
            self.assertEqual(len(pd.read_csv(folder/"generation.csv")),10)
            with self.assertRaises(FileExistsError):
                build_single_dataset(**kwargs)

    def test_invalid_profiles_rejected(self):
        for kind,parameter,value in (("dwell_and_switch","pulses_per_dwell",31),
                                     ("sinusoidal","period",7.0),
                                     ("triangular_sliding","steps_per_leg",9),
                                     ("markov_agile","transition_matrix",[[.1]*4]*4),
                                     ("markov_agile","pri_levels",[850,925,1000,1075,1150]),
                                     ("markov_agile","transition_matrix",[[1,0,0,0]]*4)):
            profile=copy.deepcopy(get_fixed_profile(kind,self.profiles["fixed_profiles"]))
            profile["pri_args"][parameter]=value
            with self.assertRaises(ValueError):validate_profile(kind,profile)


if __name__ == "__main__":
    unittest.main()
