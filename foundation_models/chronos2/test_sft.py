"""Boundary training, split isolation, budgets, checkpoint/resume and comparisons."""
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile
from unittest.mock import patch

import numpy as np
import pandas as pd

from dataset_generator.catalog import PROJECT_ROOT
from dataset_generator.generate_datasets import load_all_configs, build_single_dataset
from dataset_generator.sequence_io import SCHEMA_V2
from foundation_models.chronos2 import run_sft
from foundation_models.chronos2.compare_sft import comparison_rows
from foundation_models.chronos2.run_zero_shot import prepare_inputs, write_json
from foundation_models.chronos2.test_zero_shot import LastValuePipeline
from foundation_models.common.dataset import load_split


class SFTTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.errors, cls.profiles, _ = load_all_configs(PROJECT_ROOT/'configs')

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base/'data/single_radar'
        self.folder = self.root/'fixed/markov_agile/10x96_error_lv7'
        with redirect_stdout(StringIO()):
            build_single_dataset(self.root.parent, 'markov_agile', 'fixed', 'error_lv7', 10, 96, 123,
                                 self.errors['error_lv7'], self.profiles, protocol=SCHEMA_V2,
                                 context_intervals=64, max_horizon=32)
        self.limits = {'train':2,'val':1}

    def audit(self):
        return run_sft.audit_inputs(self.root,'10x96','fixed',['markov_agile'],['error_lv7'],self.limits)

    def reference(self):
        with redirect_stdout(StringIO()):
            _, manifest = prepare_inputs(self.root,'10x96',['fixed'],['markov_agile'],['error_lv7'],
                                         [16,64],32,'boundary',20261116,None,'seq_0008')
        reference = self.base/'zero'
        write_json(reference/'run_config.json',dict(regime='zero_shot',window_mode='boundary',model_id='mock'))
        write_json(reference/'test_windows.json',manifest)
        pd.DataFrame([dict(task=t,context_len=l,profile='fixed',radar_type='markov_agile',
                           error_level='error_lv7',num_sequences=2)
                      for t in ('PRI','Frequency','multivariate') for l in (16,64)]).to_csv(reference/'metrics.csv',index=False)
        return reference,manifest

    def test_training_audit_excludes_test_and_detects_changed_train(self):
        first=self.audit()
        self.assertEqual(first['counts'],{'train':2,'val':1})
        self.assertTrue(all('/test/' not in key for key in first['sequence_sha256']))
        path=self.folder/'train/seq_0000.csv'
        path.write_bytes(path.read_bytes()+b'\n')
        self.assertNotEqual(first,self.audit())

    def test_overlapping_and_incomplete_splits_fail(self):
        (self.folder/'val/seq_0007.csv').rename(self.folder/'val/seq_0000.csv')
        with self.assertRaisesRegex(ValueError,'overlap'):self.audit()
        (self.folder/'val/seq_0000.csv').unlink()
        with self.assertRaisesRegex(ValueError,'Incomplete'):self.audit()

    def test_training_pool_matches_observed_context_and_consecutive_future(self):
        with redirect_stdout(StringIO()):
            pool=run_sft.load_pool(self.root,'10x96','fixed','multivariate',16,32,
                                   ['markov_agile'],['error_lv7'],'train',2)
        loaded=load_split(self.folder,'train','multivariate',16,32,2,window_mode='boundary')
        for array,window in zip(pool,loaded.windows):
            self.assertEqual(array.shape,(5,48))
            np.testing.assert_array_equal(array[:,:16],window.context)
            np.testing.assert_array_equal(array[:,16:],window.target)
            self.assertEqual(window.start,48)
        with self.assertRaisesRegex(ValueError,'train or val'):
            run_sft.load_pool(self.root,'10x96','fixed','PRI',16,32,['markov_agile'],['error_lv7'],'test',1)

    def test_installed_chronos_samples_only_the_intended_boundary(self):
        from chronos.chronos2.dataset import Chronos2Dataset, DatasetMode
        import torch
        observed=np.arange(80,dtype=np.float32).reshape(5,16)
        future=np.arange(160,dtype=np.float32).reshape(5,32)+1000
        dataset=Chronos2Dataset([np.concatenate([observed,future],axis=1)],context_length=16,
                               prediction_length=32,batch_size=5,output_patch_size=16,
                               min_past=16,mode=DatasetMode.TRAIN)
        for _ in range(10):
            context,target,_,_=dataset._construct_slice(0)
            torch.testing.assert_close(context,torch.from_numpy(observed))
            torch.testing.assert_close(target,torch.from_numpy(future))

    def test_batch_budget_counts_variates_and_rounds_whole_tasks(self):
        self.assertEqual(run_sft.step_budget(44800,'PRI',20,3,None),(6720,20))
        self.assertEqual(run_sft.step_budget(44800,'multivariate',20,3,None),(33600,4))
        self.assertEqual(run_sft.step_budget(10,'multivariate',6,3,None),(15,2))
        self.assertEqual(run_sft.step_budget(10,'PRI',20,3,2),(2,20))

    def test_reference_rejects_changed_windows_and_data(self):
        reference,manifest=self.reference()
        run_sft.verify_reference(manifest,reference,'mock')
        key=next(iter(manifest['windows']))
        manifest['windows'][key]+=1
        with self.assertRaisesRegex(ValueError,'windows'):run_sft.verify_reference(manifest,reference,'mock')
        manifest['windows'][key]-=1
        manifest['sequence_sha256'][next(iter(manifest['sequence_sha256']))]='changed'
        with self.assertRaisesRegex(ValueError,'sequence_sha256'):run_sft.verify_reference(manifest,reference,'mock')

    def test_saved_adapter_tampering_is_detectable(self):
        folder=self.base/'adapter'
        write_json(folder/'adapter_config.json',{'r':16})
        (folder/'adapter_model.safetensors').write_bytes(b'first')
        before=run_sft.checkpoint_hashes(folder)
        (folder/'adapter_model.safetensors').write_bytes(b'second')
        self.assertNotEqual(before,run_sft.checkpoint_hashes(folder))
        (folder/'adapter_model.safetensors').unlink()
        with self.assertRaisesRegex(ValueError,'incomplete'):run_sft.checkpoint_hashes(folder)

    def test_dry_run_does_not_read_data_or_load_model(self):
        with patch.object(sys,'argv',['run_sft','--dry-run','--zero-shot-run','missing']), \
             patch.object(run_sft,'prepare_inputs',side_effect=AssertionError('read')), \
             patch.object(run_sft,'load_pipeline',side_effect=AssertionError('model')),redirect_stdout(StringIO()) as log:
            run_sft.main()
        self.assertIn('24 adapters; 1536 evaluation conditions',log.getvalue())

    def test_runner_resume_reuses_adapters_and_rejects_modified_training_input(self):
        reference,_=self.reference()
        out=self.base/'results'
        args=['run_sft','--zero-shot-run',str(reference),'--datasets-root',str(self.root),'--dataset-size','10x96',
              '--profiles','fixed','--tasks','PRI','multivariate','--context-lens','16','64','--horizon','32',
              '--radar-types','markov_agile','--error-levels','error_lv7','--model-id','mock',
              '--plot-sequence-id','seq_0008','--smoke-test','--no-plots','--device','cpu',
              '--output-dir',str(out),'--model-output-dir',str(self.base/'models')]
        def fit(args,task,length,profile,job,inputs):
            ckpt=args.model_output_dir/task/str(length)/profile
            write_json(ckpt/'adapter_config.json',{})
            (ckpt/'adapter_model.safetensors').write_bytes(b'fake for orchestration test')
            write_json(job/'training_complete.json',dict(checkpoint=str(ckpt),sha256=run_sft.checkpoint_hashes(ckpt)))
            return ckpt
        with patch.object(sys,'argv',args),patch.object(run_sft,'fit_adapter',side_effect=fit) as trainer, \
             patch.object(run_sft,'load_pipeline',return_value=LastValuePipeline()),redirect_stdout(StringIO()):
            run_sft.main()
        self.assertEqual(trainer.call_count,4)
        self.assertEqual(json.loads((out/'completed.json').read_text())['conditions'],4)
        self.assertIn('LoRA SFT',(out/'report.md').read_text())
        with patch.object(sys,'argv',args+['--resume']), \
             patch.object(run_sft,'fit_adapter',side_effect=AssertionError('retrained')), \
             patch.object(run_sft,'load_pipeline',return_value=LastValuePipeline()),redirect_stdout(StringIO()):
            run_sft.main()
        path=self.folder/'train/seq_0000.csv';path.write_bytes(path.read_bytes()+b'\n')
        with patch.object(sys,'argv',args+['--resume']),redirect_stdout(StringIO()):
            with self.assertRaisesRegex(ValueError,'Training inputs changed'):run_sft.main()

    def test_zero_shot_sft_pairing_keeps_target_profile_and_context(self):
        from dataset_generator.catalog import RADAR_TYPES,ERROR_LEVELS
        zero={('multivariate',992,'varying',radar,level):{'mae_pri':0,'mae_frequency':4}
              for radar in RADAR_TYPES for level in ERROR_LEVELS}
        sft={key:{'mae_pri':2,'mae_frequency':1} for key in zero}
        pri=comparison_rows(zero,sft,'multivariate','PRI','varying',992)
        freq=comparison_rows(zero,sft,'multivariate','Frequency','varying',992)
        self.assertEqual(len(pri),64)
        self.assertEqual(pri[0]['delta_right_minus_left'],2)
        self.assertEqual(freq[0]['delta_right_minus_left'],-3)

    def test_sft_workbook_has_sft_label_and_separate_name(self):
        from foundation_models.chronos2 import compare_context_mae as tables
        rows={profile:[['Univariate','PRI','stagger','clean',1,2,3,4,'us']] for profile in ('fixed','varying')}
        with patch.object(tables,'OUT',self.base):
            tables.write_xlsx(rows,'new_complex_pri','lora_sft')
        path=self.base/'new_complex_pri_chronos2_lora_sft_mae.xlsx'
        with zipfile.ZipFile(path) as book:
            xml=book.read('xl/worksheets/sheet1.xml').decode()
        self.assertIn('LoRA SFT MAE',xml)
        self.assertNotIn('zero-shot MAE',xml)

    def test_sft_comparison_rejects_unpaired_or_incomplete_manifests(self):
        from foundation_models.chronos2.compare_sft import validate_pair
        from dataset_generator.catalog import RADAR_TYPES,ERROR_LEVELS
        zero,sft=self.base/'zero',self.base/'sft'
        config=dict(dataset_family='new_complex_pri',dataset_size='1000x1056',window_mode='boundary',
                    horizon=32,max_test_seqs=None,context_lens=[96,256,512,992],profiles=['fixed','varying'],
                    tasks=['PRI','Frequency','multivariate'],radar_types=RADAR_TYPES,error_levels=ERROR_LEVELS,
                    model_id='mock')
        manifest=dict(meta={'schema_version':SCHEMA_V2},windows={},sequence_sha256={},
                      metadata_sha256={},sequence_lengths={},plot_sequences={})
        for root,regime in ((zero,'zero_shot'),(sft,'lora_sft')):
            write_json(root/'run_config.json',{**config,'regime':regime})
            write_json(root/'test_windows.json',manifest)
        with self.assertRaisesRegex(ValueError,'Incomplete'):validate_pair(zero,sft)
        manifest['windows']['different']=1
        write_json(sft/'test_windows.json',manifest)
        with self.assertRaisesRegex(ValueError,'windows differ'):validate_pair(zero,sft)


if __name__=='__main__':unittest.main()
