"""Compare full Chronos-2 SFT and zero-shot runs on identical test windows."""
from __future__ import annotations

import argparse
import csv
import itertools
import json
from pathlib import Path

from dataset_generator.catalog import NEW_COMPLEX_PRI, PROJECT_ROOT, RADAR_TYPES, ERROR_LEVELS, SCHEMA_V2
from foundation_models.common.windowing import file_sha256
from foundation_models.chronos2.plot_mae_comparisons import (
    CONTEXTS, index_metrics, verify_sequence_scores, plot_comparison, write_csv,
)


def validate_pair(zero: Path, sft: Path) -> tuple[dict, dict]:
    configs = [json.loads((root/'run_config.json').read_text()) for root in (zero, sft)]
    if [c['regime'] for c in configs] != ['zero_shot', 'lora_sft']:
        raise ValueError('Expected zero-shot followed by LoRA SFT')
    for c in configs:
        if (c['dataset_family'] != NEW_COMPLEX_PRI or c['dataset_size'] != '1000x1056'
                or c['window_mode'] != 'boundary' or c['horizon'] != 32
                or c['max_test_seqs'] is not None or c.get('smoke_test', False)
                or c.get('max_train_seqs_per_dataset') is not None
                or c.get('max_val_seqs_per_dataset') is not None):
            raise ValueError('Comparison requires full new_complex_pri boundary runs')
        for key, expected in [('context_lens', CONTEXTS), ('profiles', ('fixed','varying')),
                              ('tasks', ('PRI','Frequency','multivariate')),
                              ('radar_types',RADAR_TYPES), ('error_levels',ERROR_LEVELS)]:
            if len(c[key]) != len(expected) or set(c[key]) != set(expected):
                raise ValueError(f'Incomplete matrix: {key}')
    if configs[0]['model_id'] != configs[1]['model_id']:
        raise ValueError('Base model IDs differ')
    manifests = [json.loads((root/'test_windows.json').read_text()) for root in (zero, sft)]
    for m in manifests:
        if m['meta']['schema_version'] != SCHEMA_V2:
            raise ValueError('Unexpected schema')
    for key in ('windows','sequence_sha256','metadata_sha256','sequence_lengths','plot_sequences'):
        if manifests[0][key] != manifests[1][key]:
            raise ValueError(f'Test inputs/windows differ: {key}')
    expected_sequences = {f'{profile}/{radar}/{level}/seq_{i:04d}'
                          for profile,radar,level in itertools.product(('fixed','varying'),RADAR_TYPES,ERROR_LEVELS)
                          for i in range(800,1000)}
    expected_windows = {f'{key}/{length}':1024-length for key in expected_sequences for length in CONTEXTS}
    for m in manifests:
        if set(m['sequence_sha256']) != expected_sequences or m['windows'] != expected_windows:
            raise ValueError('Incomplete or incorrectly aligned test-window manifest')
        if set(m['sequence_lengths']) != expected_sequences or set(m['sequence_lengths'].values()) != {1056}:
            raise ValueError('Incomplete sequence-length manifest')
    saved = json.loads((sft/'zero_shot_reference.json').read_text())
    if saved != {name:file_sha256(zero/name) for name in ('run_config.json','test_windows.json','metrics.csv')}:
        raise ValueError('Zero-shot reference changed after SFT preflight')
    lookups = []
    for root, config in zip((zero,sft),configs):
        with (root/'metrics.csv').open(newline='',encoding='utf-8-sig') as f:
            lookup = index_metrics(list(csv.DictReader(f)),config)
        verify_sequence_scores(root,lookup)
        lookups.append(lookup)
    return tuple(lookups)


def comparison_rows(zero: dict, sft: dict, task: str, target: str, profile: str, length: int) -> list[dict]:
    metric = f'mae_{target.lower()}' if task == 'multivariate' else 'mae'
    result = []
    for radar, level in itertools.product(RADAR_TYPES,ERROR_LEVELS):
        key = (task,length,profile,radar,level)
        left,right = float(zero[key][metric]),float(sft[key][metric])
        result.append(dict(dataset_family=NEW_COMPLEX_PRI,comparison='zero_shot_vs_sft',
                           regime_label='zero-shot vs LoRA SFT',task=task,target=target,context_len=length,
                           horizon=32,held_setting=f'{profile}, {"multivariate" if task=="multivariate" else "univariate"}',
                           profile=profile,radar_type=radar,error_level=level,left_label='Zero-shot',right_label='LoRA SFT',
                           mae_left=left,mae_right=right,delta_right_minus_left=right-left,
                           unit='us' if target=='PRI' else 'MHz',test_sequences_each=200))
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--zero-shot-run',type=Path,required=True)
    p.add_argument('--sft-run',type=Path,required=True)
    p.add_argument('--output-dir',type=Path)
    args=p.parse_args()
    zero,sft=args.zero_shot_run.resolve(),args.sft_run.resolve()
    output=(args.output_dir or PROJECT_ROOT/'outputs'/NEW_COMPLEX_PRI/'sft_vs_zero_shot'/sft.name).resolve()
    if any(output==root or output in root.parents or root in output.parents for root in (zero,sft)):
        p.error('Comparison output must be separate from source experiments')
    if output.exists() and any(output.iterdir()):
        p.error('Use a fresh comparison output directory')
    hashes={str(root/name):file_sha256(root/name) for root in (zero,sft)
            for name in ('run_config.json','test_windows.json','metrics.csv')}
    left,right=validate_pair(zero,sft)
    output.mkdir(parents=True,exist_ok=True)
    all_rows=[]
    readme=['# new_complex_pri: zero-shot vs LoRA SFT','',
            'Same test CSV hashes, context/target windows, metrics and 200 sequences per condition.',
            'H=32. Each L, target, profile and input task is plotted separately.',
            'Negative SFT minus zero-shot MAE means SFT improved. No radar/error averages.','']
    for length,profile in itertools.product(CONTEXTS,('fixed','varying')):
        for task,target in [('PRI','PRI'),('Frequency','Frequency'),('multivariate','PRI'),('multivariate','Frequency')]:
            rows=comparison_rows(left,right,task,target,profile,length)
            png=output/f'L{length}'/f'new_complex_pri_{profile}_{task.lower()}_{target.lower()}_L{length}.png'
            plot_comparison(png,rows)
            write_csv(png.with_suffix('.csv'),rows)
            readme.append(f'- [{profile}, {task}, {target}, L={length}]({png.relative_to(output).as_posix()})')
            all_rows.extend(rows)
    write_csv(output/'comparisons.csv',all_rows)
    (output/'README.md').write_text('\n'.join(readme)+'\n',encoding='utf-8')
    if any(file_sha256(Path(name)) != value for name,value in hashes.items()):
        raise ValueError('Source experiment changed during comparison')
    print(f'[DONE] 32 comparison PNGs, {len(all_rows)} paired MAE rows: {output}')


if __name__=='__main__':main()
