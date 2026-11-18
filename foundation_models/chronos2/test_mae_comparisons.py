"""Checks comparison pairing so profile, task, and target cannot get crossed."""
import unittest

from foundation_models.chronos2.plot_mae_comparisons import index_metrics, pair_condition


class MAEComparisonTest(unittest.TestCase):
    def setUp(self):
        self.config={"tasks":["PRI","Frequency","multivariate"],"context_lens":[96],
                     "profiles":["fixed","varying"],"radar_types":["stagger"],"error_levels":["clean"],"horizon":32}
        self.rows=[]
        for profile,factor in (("fixed",1),("varying",2)):
            for task in self.config["tasks"]:
                row={"task":task,"context_len":96,"horizon":32,"profile":profile,"radar_type":"stagger",
                     "error_level":"clean","num_sequences":200,"valid_pulses_evaluated":6400,
                     "skipped_short":0,"skipped_no_emitter":0}
                row.update({"mae_pri":100*factor,"mae_frequency":300*factor} if task=="multivariate" else {"mae":(10 if task=="PRI" else 30)*factor})
                self.rows.append(row)
        self.lookup=index_metrics(self.rows,self.config)

    def pair(self,kind,target,held):
        return pair_condition(self.lookup,kind,target,held,96,"stagger","clean")

    def test_fixed_varying_holds_task_and_target_constant(self):
        r=self.pair("fixed_vs_varying","PRI","univariate")
        self.assertEqual((r["mae_left"],r["mae_right"],r["delta_right_minus_left"]),(10,20,10))
        r=self.pair("fixed_vs_varying","Frequency","multivariate")
        self.assertEqual((r["mae_left"],r["mae_right"],r["unit"]),(300,600,"MHz"))

    def test_univariate_multivariate_holds_profile_and_target_constant(self):
        r=self.pair("univariate_vs_multivariate","PRI","varying")
        self.assertEqual((r["mae_left"],r["mae_right"]),(20,200))
        r=self.pair("univariate_vs_multivariate","Frequency","fixed")
        self.assertEqual((r["mae_left"],r["mae_right"]),(30,300))

    def test_zero_mae_is_not_treated_as_missing(self):
        for row in self.lookup.values():
            for key in ("mae","mae_pri","mae_frequency"):
                if key in row:row[key]=0
        r=self.pair("univariate_vs_multivariate","PRI","fixed")
        self.assertEqual((r["mae_left"],r["mae_right"],r["delta_right_minus_left"]),(0,0,0))

    def test_duplicate_missing_and_nonfinite_conditions_are_rejected(self):
        with self.assertRaisesRegex(ValueError,"Duplicate"):index_metrics(self.rows+[self.rows[0]],self.config)
        with self.assertRaisesRegex(ValueError,"matrix"):index_metrics(self.rows[:-1],self.config)
        self.rows[0]["mae"]=float("nan")
        with self.assertRaisesRegex(ValueError,"Invalid MAE"):index_metrics(self.rows,self.config)

    def test_invalid_factor_combinations_are_rejected(self):
        with self.assertRaises(ValueError):self.pair("fixed_vs_varying","PRI","fixed")
        with self.assertRaises(ValueError):self.pair("univariate_vs_multivariate","PRI","univariate")


if __name__=="__main__":unittest.main()
