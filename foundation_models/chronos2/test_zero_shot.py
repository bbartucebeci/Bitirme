"""Offline checks for the dedicated zero-shot experiment, without model downloads."""
import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from foundation_models.chronos2.run_zero_shot import prepare_inputs, evaluate_one, export_reports, main


class LastValuePipeline:
    """Deterministic inference double to check input/target/report wiring."""
    def __init__(self):
        self.contexts = []

    def predict_quantiles(self, inputs, prediction_length, quantile_levels, batch_size, context_length):
        assert quantile_levels == [.5]
        self.contexts.extend([array.copy() for array in inputs])
        return None, [np.repeat(array[:, -1:], prediction_length, axis=1) for array in inputs]


class ZeroShotExperimentTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.root = self.base/"single_radar"
        for profile in ("fixed","varying"):
            folder = self.root/profile/"markov_agile"/"10x1024_clean"
            (folder/"test").mkdir(parents=True)
            metadata = {"profile_mode":profile,"radar_type":"markov_agile","error_level":"clean",
                        "sequence_count":10,"expected_pulses_per_sequence":1024,
                        "split":{"train":{"sequence_count":7},"val":{"sequence_count":1},"test":{"sequence_count":2}}}
            (folder/"metadata.yaml").write_text(yaml.safe_dump(metadata),encoding="utf-8")
            for sid in ("seq_0008","seq_0009"):
                indices = np.arange(1025)
                pd.DataFrame({"sequence_id":sid,"pulse_index":indices,"Radar_ID":"R_SINGLE",
                              "PRI":800.+indices/4,"Measured_Delta_TOA":np.r_[0,1000.+indices[1:]/2],
                              "Frequency":9000.+indices/100,"PW":1.5,"AOA":45.,"Amplitude":-55.}).to_csv(folder/"test"/f"{sid}.csv",index=False)

    def manifest(self,mode="tail",plot_id=None):
        return prepare_inputs(self.root,"10x1024",("fixed","varying"),("markov_agile",),
                              ("clean",),(96,992),32,mode,20261116,None,plot_id)

    def evaluate(self,task="PRI",length=96,mode="tail"):
        _,manifest = self.manifest(mode)
        pipeline = LastValuePipeline()
        folder = self.root/"fixed/markov_agile/10x1024_clean"
        output = self.base/"output"/task/f"L{length}"/"fixed"
        row = evaluate_one(pipeline,folder,"fixed","markov_agile","clean",task,length,32,
                           2,None,mode,20261116,manifest,output,False)
        return row,pipeline,output

    def test_tail_windows_have_same_targets_and_input_contract(self):
        coverage,manifest = self.manifest()
        self.assertEqual(len(coverage),2)
        self.assertEqual(len(manifest["sequence_sha256"]),4)
        self.assertEqual(manifest["windows"]["fixed/markov_agile/clean/seq_0008/96"],896)
        self.assertEqual(manifest["windows"]["fixed/markov_agile/clean/seq_0008/992"],0)
        examples = []
        for length in (96,992):
            row,pipeline,out = self.evaluate(length=length)
            self.assertEqual(row["num_sequences"],2)
            self.assertEqual(row["valid_pulses_evaluated"],64)
            self.assertEqual(pipeline.contexts[0].shape,(1,length))
            examples.append(json.loads((out/"examples/markov_agile_clean.json").read_text()))
        np.testing.assert_array_equal(examples[0]["target"],examples[1]["target"])
        self.assertEqual(examples[0]["context"][0][-1],1496.)
        self.assertEqual(examples[0]["target"][0][0],1048.25)
        expected_error=np.abs(1496.-np.asarray(examples[0]["target"][0])).mean()
        self.assertAlmostEqual(row["mae"],expected_error)

    def test_frequency_univariate_and_multivariate_primary_scores(self):
        row,pipeline,out = self.evaluate(task="Frequency")
        self.assertEqual(pipeline.contexts[0].shape,(1,96))
        self.assertAlmostEqual(float(pipeline.contexts[0][0,-1]),9009.92,places=2)
        row,pipeline,out = self.evaluate(task="multivariate")
        self.assertEqual(pipeline.contexts[0].shape,(5,96))
        for key in ("mae_pri","rmse_pri","hit_rate_pri","mae_frequency","rmse_frequency","hit_rate_frequency"):
            self.assertIn(key,row)
        self.assertNotIn("mae_pw",row)
        self.assertNotIn("mae_aoa",row)
        self.assertEqual(len(pd.read_csv(out/"per_sequence/markov_agile_clean.csv")),2)

    def test_random_manifest_is_deterministic_and_matches_evaluation(self):
        _,a = self.manifest("random")
        _,b = self.manifest("random")
        self.assertEqual(a,b)
        _,_,out = self.evaluate(mode="random")
        example=json.loads((out/"examples/markov_agile_clean.json").read_text())
        self.assertEqual(example["start"],a["windows"]["fixed/markov_agile/clean/seq_0008/96"])

    def test_changed_csv_and_unselected_plot_sequence_fail(self):
        with self.assertRaisesRegex(ValueError,"outside selected"):
            self.manifest(plot_id="seq_0007")
        _,manifest=self.manifest()
        folder=self.root/"fixed/markov_agile/10x1024_clean"
        csv=folder/"test/seq_0008.csv"
        frame=pd.read_csv(csv);frame.loc[1,"Frequency"]+=1;frame.to_csv(csv,index=False)
        with self.assertRaisesRegex(ValueError,"CSV changed"):
            evaluate_one(LastValuePipeline(),folder,"fixed","markov_agile","clean","PRI",96,32,
                         2,None,"tail",20261116,manifest,self.base/"output",False)

    def test_reports_keep_radar_error_and_context_keys(self):
        rows=[]
        for task in ("PRI","Frequency","multivariate"):
            row,_,_=self.evaluate(task=task)
            rows.append(row)
        output=self.base/"reports";output.mkdir()
        config={"horizon":32,"window_mode":"tail"}
        frame=export_reports(rows,output,config)
        self.assertEqual(len(frame),3)
        self.assertTrue((output/"multivariate/L96/fixed/report.md").is_file())
        self.assertTrue((output/"by_radar/PRI/markov_agile/report.md").is_file())
        self.assertIn("No fitting",(output/"report.md").read_text())

    def test_coverage_cli_never_loads_model_and_resume_checks_inputs(self):
        output=self.base/"coverage"
        argv=["run_zero_shot","--datasets-root",str(self.root),"--dataset-size","10x1024",
              "--radar-types","markov_agile","--error-levels","clean","--context-lens","96","992",
              "--coverage-only","--output-dir",str(output)]
        with patch("sys.argv",argv), patch("foundation_models.chronos2.run_zero_shot.load_pipeline") as load:
            main()
            load.assert_not_called()
        self.assertEqual(len(pd.read_csv(output/"coverage.csv")),2)
        with patch("sys.argv",argv+["--resume"]):
            main()
        # An interrupted run may resume only against exactly the same CSV bytes.
        csv=self.root/"fixed/markov_agile/10x1024_clean/test/seq_0008.csv"
        csv.write_bytes(csv.read_bytes()+b"\n")
        with patch("sys.argv",argv+["--resume"]),self.assertRaises(SystemExit) as error:
            main()
        self.assertEqual(error.exception.code,2)

    def test_coverage_rejects_incomplete_test_split(self):
        (self.root/"varying/markov_agile/10x1024_clean/test/seq_0009.csv").unlink()
        with self.assertRaisesRegex(ValueError,"expected 2 test CSVs"):
            self.manifest()


if __name__=="__main__":unittest.main()
