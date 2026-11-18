"""Source identity, whole-PDW loss/restoration, storage and boundary regression checks."""
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd
import yaml

from dataset_generator.catalog import RADAR_TYPES, PROJECT_ROOT
from dataset_generator.consecutive_future import assemble_source_stream, generate_consecutive_sequence
from dataset_generator.generate_datasets import build_single_dataset, get_fixed_profile, load_all_configs
from dataset_generator.sequence_io import SCHEMA_V2, boundary_start, read_sequence_frame
from dataset_generator.validate_datasets import validate_source_storage


class ConsecutiveFutureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.errors,cls.profiles,_=load_all_configs(PROJECT_ROOT/"configs")

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)

    def toy_source(self):
        ids=np.arange(20)
        return pd.DataFrame({"source_pulse_id":ids,"Radar_ID":"R_SINGLE","TOA":np.cumsum(800.+ids),
                             "PRI":800.+ids,"Frequency":9000.+ids,"PW":1.+ids/100,
                             "Amplitude":-60.+ids/10,"AOA":20.+ids})

    def test_whole_row_loss_and_restore_for_both_masks(self):
        source=self.toy_source()
        for loss_kind in ("poi","global"):
            with self.subTest(loss_kind=loss_kind):
                poi=np.ones(len(source),dtype=bool);glob=poi.copy()
                selected=poi if loss_kind=="poi" else glob
                selected[[2,7]]=False
                raw=assemble_source_stream(source,poi,glob,4,4)
                path=self.root/f'{loss_kind}.csv';raw.to_csv(path,index=False)
                frame=read_sequence_frame(path)
                # Source 2 is absent in every context channel; source 7 is restored in every future channel.
                expected_ids=[0,1,3,4,5,6,7,8,9]
                self.assertEqual(frame.source_pulse_id.tolist(),expected_ids)
                for channel in ("TOA","PRI","Frequency","PW","Amplitude","AOA"):
                    np.testing.assert_allclose(frame[channel],source.loc[expected_ids,channel])
                self.assertEqual(raw.loc[2,"sequence_index"],-1)
                self.assertFalse(raw.loc[7,"observed_keep"])
                self.assertEqual(raw.loc[7,"segment"],"horizon")
                np.testing.assert_allclose(frame.Measured_Delta_TOA,np.r_[0,np.diff(frame.TOA)])
                self.assertAlmostEqual(frame.Measured_Delta_TOA.iloc[2],source.PRI.iloc[2]+source.PRI.iloc[3])

    def build(self,max_horizon=64):
        build_single_dataset(self.root,"markov_agile","fixed","error_lv7",10,1024,123,
                             self.errors["error_lv7"],self.profiles,protocol=SCHEMA_V2,
                             context_intervals=1024,max_horizon=max_horizon)
        return self.root/f"single_radar/fixed/markov_agile/10x{1024+max_horizon}_error_lv7"

    def test_one_copy_storage_and_explicit_boundary_windows(self):
        from foundation_models.common.dataset import load_split,load_dataset_sequences,load_multivariate_dataset_sequences
        from foundation_models.chronos2.run_zero_shot import prepare_inputs,evaluate_one
        from foundation_models.chronos2.test_zero_shot import LastValuePipeline
        from classic_methods.common import load_sequence_arrays,extract_window
        folder=self.build();metadata=yaml.safe_load((folder/"metadata.yaml").read_text())
        self.assertFalse(list(folder.rglob("sequences.csv")))
        self.assertEqual(len(list(folder.glob("*/seq_*.csv"))),10)
        for split,count in (("train",7),("val",1),("test",2)):
            self.assertEqual(metadata["split"][split],{"sequence_count":count,"row_count":count*1089})
        path=folder/"test/seq_0008.csv";raw=pd.read_csv(path);frame=read_sequence_frame(path)
        self.assertGreater(len(raw),len(frame))
        self.assertEqual(len(frame),1089)
        record=pd.read_csv(folder/"generation.csv").set_index("sequence_id").loc["seq_0008"]
        self.assertGreater(validate_source_storage(raw,frame,metadata,record,path),0)
        for length in (96,128,256,512,992,1024):
            full=load_split(folder,"test","multivariate",length,64,window_mode="boundary")
            short=load_split(folder,"test","multivariate",length,32,window_mode="boundary")
            self.assertEqual(full.windows[0].start,1024-length)
            np.testing.assert_array_equal(full.windows[0].context,short.windows[0].context)
            np.testing.assert_array_equal(short.windows[0].target,full.windows[0].target[:,:32])
            np.testing.assert_array_equal(short.windows[0].target[0],frame.PRI.to_numpy()[1025:1057].astype(np.float32))
            a,b,m=load_sequence_arrays(path)
            c,t,_=extract_window(a,b,m,length,32,1024-length)
            np.testing.assert_array_equal(short.windows[0].context[0],c.astype(np.float32))
            np.testing.assert_array_equal(short.windows[0].target[0],t.astype(np.float32))
        for wrong_mode in ("tail","first","random"):
            with self.assertRaisesRegex(ValueError,"requires --window-mode boundary"):
                load_split(folder,"test","PRI",96,32,window_mode=wrong_mode)
        with self.assertRaises(ValueError):load_split(folder,"test","PRI",1025,32,window_mode="boundary")
        with self.assertRaises(ValueError):load_split(folder,"test","PRI",96,65,window_mode="boundary")
        for legacy in (load_dataset_sequences,load_multivariate_dataset_sequences):
            with self.assertRaisesRegex(ValueError,"legacy first-window loader"):legacy(folder)
        coverage,manifest=prepare_inputs(self.root/"single_radar","10x1088",["fixed"],["markov_agile"],
                                         ["error_lv7"],[96,1024],32,"boundary",123,None,None)
        pipeline=LastValuePipeline()
        row=evaluate_one(pipeline,folder,"fixed","markov_agile","error_lv7","multivariate",96,32,2,None,
                         "boundary",123,manifest,self.root/"result",False)
        self.assertEqual(row["num_sequences"],2)

    def test_all_radar_laws_continue_through_restored_future(self):
        for radar in RADAR_TYPES:
            profile=get_fixed_profile(radar,self.profiles["fixed_profiles"])
            results=[]
            for repeat in range(2):
                np.random.seed(99)
                results.append(generate_consecutive_sequence(radar,profile,self.errors["error_lv7"],"seq_0000",
                                                              "error_lv7",1024,64,555))
            pd.testing.assert_frame_equal(*results)
            raw=results[0]
            selected=raw[raw.sequence_index>=0]
            context=selected[selected.segment=="context"]
            future=selected[selected.segment=="horizon"]
            self.assertEqual(len(context),1024)
            self.assertEqual(len(future),64)
            self.assertTrue(context.observed_keep.all())
            self.assertGreater(int((~future.observed_keep).sum()),0)
            self.assertEqual(future.source_pulse_id.iloc[0],context.source_pulse_id.iloc[-1]+1)
            np.testing.assert_array_equal(np.diff(future.source_pulse_id),np.ones(63))
            if radar=="markov_agile":
                from dataset_generator.generate_datasets import RADAR_CLASSES
                init=raw.attrs["initialization"]
                transmitter=RADAR_CLASSES[radar]("R_SINGLE",freq_mean=9000.,**profile["pri_args"],**init)
                np.testing.assert_array_equal(raw.PRI,transmitter.source_pris(len(raw)))

    def test_hopping_frequency_advances_during_context_losses(self):
        profile=get_fixed_profile("stagger",self.profiles["fixed_profiles"])
        pool=[8800.+i for i in range(512)]
        profile.update(freq_mode="hopping",freq_hopping_values=pool)
        errors=dict(self.errors["clean"],poi=.5,global_drop_rate=.2)
        np.random.seed(101)
        raw=generate_consecutive_sequence("stagger",profile,errors,"seq_0000","controlled",64,32,900)
        np.testing.assert_array_equal(raw.Frequency,np.asarray(pool)[raw.source_pulse_id%len(pool)])
        context=raw[raw.segment.eq("context")]
        self.assertTrue((np.diff(context.source_pulse_id)>1).any())
        np.testing.assert_array_equal(context.Frequency,np.asarray(pool)[context.source_pulse_id%len(pool)])
        future=raw[raw.segment.eq("horizon")]
        self.assertTrue((~future.observed_keep).any())
        np.testing.assert_array_equal(future.Frequency,np.asarray(pool)[future.source_pulse_id%len(pool)])

    def test_source_id_and_projection_corruption_are_rejected(self):
        source=self.toy_source();mask=np.ones(len(source),dtype=bool)
        source.loc[3,"source_pulse_id"]=100
        with self.assertRaisesRegex(ValueError,"consecutive"):
            assemble_source_stream(source,mask,mask,4,4)
        raw=assemble_source_stream(self.toy_source(),mask,mask,4,4)
        raw.loc[2,"sequence_index"]=1
        p=self.root/"bad.csv";raw.to_csv(p,index=False)
        with self.assertRaisesRegex(ValueError,"not contiguous"):read_sequence_frame(p)

    def test_unified_training_loaders_use_the_same_boundary(self):
        from foundation_models.common.dataset import create_unified_pdw_dataloader,create_unified_multivariate_dataloader,load_split
        folder=self.build()
        expected=load_split(folder,"train","multivariate",96,32,1,window_mode="boundary").windows[0]
        for factory,channels in ((create_unified_pdw_dataloader,1),(create_unified_multivariate_dataloader,5)):
            loader=factory(self.root/"single_radar/fixed",radar_types=["markov_agile"],error_levels=["error_lv7"],
                           dataset_size="10x1088",max_seqs_per_dataset=1,batch_size=1,shuffle=False)
            context,target,mask=next(iter(loader))
            np.testing.assert_array_equal(context[0].numpy(),expected.context[:channels])
            np.testing.assert_array_equal(target[0].numpy(),expected.target[0] if channels==1 else expected.target)
            self.assertTrue(mask.all())

    def test_incomplete_collections_and_nonempty_generation_roots_are_rejected(self):
        from foundation_models.chronos2.run_zero_shot import prepare_inputs
        from dataset_generator.generate_datasets import main
        folder=self.build()
        source=folder/"test/seq_0008.csv";before=source.read_bytes()
        (self.root/"collection.json").write_text(json.dumps({"status":"building"}))
        with self.assertRaisesRegex(ValueError,"collection is incomplete"):
            prepare_inputs(self.root/"single_radar","10x1088",["fixed"],["markov_agile"],
                           ["error_lv7"],[96],32,"boundary",123,None,None)
        argv=["generate_datasets","--protocol",SCHEMA_V2,"--radar-type","markov_agile",
              "--smoke-test","--output-dir",str(self.root)]
        with patch("sys.argv",argv),self.assertRaises(SystemExit) as result:
            main()
        self.assertEqual(result.exception.code,2)
        self.assertEqual(source.read_bytes(),before)

    def test_boundary_experiment_resumes_without_new_forecasts(self):
        from types import SimpleNamespace
        import torch
        from foundation_models.chronos2.run_zero_shot import main
        from foundation_models.chronos2.test_zero_shot import LastValuePipeline
        self.build()
        pipeline=LastValuePipeline()
        pipeline.model=SimpleNamespace(device=torch.device("cpu"),config=SimpleNamespace(_commit_hash="test"))
        argv=["run_zero_shot","--datasets-root",str(self.root/"single_radar"),"--dataset-size","10x1088",
              "--profiles","fixed","--radar-types","markov_agile","--error-levels","error_lv7",
              "--tasks","PRI","--context-lens","96","1024","--horizon","32","--window-mode","boundary",
              "--max-test-seqs","1","--no-plots","--device","cpu","--output-dir",str(self.root/"results")]
        with patch("foundation_models.chronos2.run_zero_shot.load_pipeline",return_value=pipeline):
            with patch("sys.argv",argv):main()
            self.assertEqual(len(pipeline.contexts),2)
            with patch("sys.argv",argv+["--resume"]):main()
            self.assertEqual(len(pipeline.contexts),2)


if __name__=="__main__":unittest.main()
