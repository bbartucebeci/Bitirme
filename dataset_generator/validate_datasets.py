"""Validate every selected single-radar capture without generating data or loading models."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import zlib

import numpy as np
import pandas as pd
import yaml

from dataset_generator.catalog import COMPLEX_DATASETS_ROOT, RADAR_TYPES, ERROR_LEVELS
from dataset_generator.generate_datasets import OUTPUT_COLUMNS, validate_profile


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_tree(root: Path, dataset_size: str, radar_types=RADAR_TYPES) -> dict:
    count, intervals = map(int, dataset_size.split("x"))
    expected = {"train": int(.7*count), "val": int(.1*count)}
    expected["test"] = count - sum(expected.values())
    summary = {"datasets": 0, "sequences": 0, "rows": 0, "split_sequences": {s:0 for s in expected},
               "radar_types": list(radar_types), "error_levels": list(ERROR_LEVELS), "profiles": ["fixed","varying"],
               "dataset_size": dataset_size, "root": str(root.resolve()), "checks": [
                   "complete condition matrix", "split membership", "sequence and combined CSV equality",
                   "1024 intervals plus anchor (or explicitly requested size)", "strictly increasing TOA",
                   "delta TOA equals TOA difference", "only real emitter pulses", "finite PDW values",
                   "profile/source parameter validation", "per-sequence seed and initialization records",
                   "profile identity across error levels", "no dataset writes"]}
    phases = {kind:set() for kind in radar_types}
    bytes_total=0
    for mode in ("fixed","varying"):
        for kind in radar_types:
            reference_profiles = None
            for level in ERROR_LEVELS:
                folder = root/mode/kind/f"{dataset_size}_{level}"
                m=yaml.safe_load((folder/"metadata.yaml").read_text(encoding="utf-8"))
                require(m["schema_version"]=="complex_pri_v1",f"{folder}: wrong schema")
                require((m["radar_type"],m["profile_mode"],m["error_level"])==(kind,mode,level),f"{folder}: identity mismatch")
                require(m["sequence_count"]==count and m["expected_pulses_per_sequence"]==intervals,f"{folder}: size mismatch")
                require(m["observed_rows_per_sequence"]==intervals+1 and m["first_row_is_anchor"],f"{folder}: anchor metadata mismatch")
                require(m["effective_freq_mode"]=="constant",f"{folder}: RF is not constant")
                require(m["error_parameters"]["noise_rate"]==0 and m["error_parameters"]["multipath_prob"]==0,f"{folder}: unwanted pulses enabled")
                records=pd.read_csv(folder/"generation.csv").set_index("sequence_id")
                require(len(records)==count and records.index.is_unique,f"{folder}: generation records mismatch")
                if mode=="varying":
                    profiles=pd.read_csv(folder/"profiles.csv").set_index("sequence_id")
                    require(len(profiles)==count and profiles.index.is_unique,f"{folder}: profiles mismatch")
                    if reference_profiles is not None:pd.testing.assert_frame_equal(profiles,reference_profiles)
                    reference_profiles=profiles
                    for sid,row in profiles.iterrows():
                        profile=row.to_dict();profile["pri_args"]=json.loads(row.pri_arguments_json)
                        validate_profile(kind,profile)
                        for key,lo,hi in (("mean_pri_us",800,1200),("freq_mean_mhz",8900,9100),
                                          ("pw_mean_us",1,2),("amp_mean_dbm",-65,-45),("aoa_mean_deg",0,360)):
                            require(lo<=profile[key]<=hi,f"{folder}/{sid}: {key} outside sampling range")
                else:validate_profile(kind,m["fixed_profile"])
                begin=0
                for split,n in expected.items():
                    ids=[f"seq_{i:04d}" for i in range(begin,begin+n)];begin+=n
                    files=sorted((folder/split).glob("seq_*.csv"))
                    require([p.stem for p in files]==ids,f"{folder}/{split}: incorrect split membership")
                    require(m["split"][split]=={"sequence_count":n,"row_count":n*(intervals+1)},f"{folder}: split metadata mismatch")
                    combined=pd.read_csv(folder/split/"sequences.csv")
                    require(len(combined)==n*(intervals+1),f"{folder}/{split}: combined length mismatch")
                    for i,p in enumerate(files):
                        frame=pd.read_csv(p)
                        require(list(frame.columns)==OUTPUT_COLUMNS,f"{p}: unexpected schema")
                        require(len(frame)==intervals+1,f"{p}: incomplete sequence")
                        require(frame.sequence_id.eq(p.stem).all() and frame.radar_type.eq(kind).all()
                                and frame.error_level.eq(level).all(),f"{p}: identity mismatch")
                        np.testing.assert_array_equal(frame.pulse_index,np.arange(intervals+1))
                        require(frame.Radar_ID.eq("R_SINGLE").all(),f"{p}: noise or echo present")
                        numeric=frame[["TOA","PRI","Frequency","PW","Amplitude","AOA","Measured_Delta_TOA"]]
                        require(np.isfinite(numeric.to_numpy()).all(),f"{p}: non-finite PDW")
                        require((np.diff(frame.TOA)>0).all() and (frame.PRI>0).all() and (frame.PW>0).all(),f"{p}: non-positive timing")
                        require(frame.AOA.between(0,360,inclusive="left").all(),f"{p}: AOA out of bounds")
                        np.testing.assert_allclose(frame.Measured_Delta_TOA,np.r_[0,np.diff(frame.TOA)],rtol=1e-10,atol=1e-7)
                        pd.testing.assert_frame_equal(frame,combined.iloc[i*(intervals+1):(i+1)*(intervals+1)].reset_index(drop=True))
                        record=records.loc[p.stem]
                        key=f"{m['seed']}|{kind}|{mode}|{level}|{intervals}|{p.stem}"
                        require(int(record.sequence_seed)==zlib.crc32(key.encode()),f"{p}: seed mismatch")
                        init=json.loads(record.initialization_json)
                        if init:phases[kind].add(json.dumps(init,sort_keys=True))
                        summary["sequences"]+=1;summary["rows"]+=len(frame)
                    summary["split_sequences"][split]+=n
                bytes_total+=sum(p.stat().st_size for p in folder.rglob("*") if p.is_file())
                summary["datasets"]+=1
    summary["bytes_on_disk"]=bytes_total
    summary["distinct_initializations"]={key:len(value) for key,value in phases.items()}
    require(summary["datasets"]==2*len(radar_types)*len(ERROR_LEVELS),"Incomplete selected condition matrix")
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--datasets-root",type=Path,default=COMPLEX_DATASETS_ROOT/"single_radar")
    parser.add_argument("--dataset-size",default="10x1024")
    parser.add_argument("--radar-types",nargs="+",choices=RADAR_TYPES,default=RADAR_TYPES)
    parser.add_argument("--report",type=Path)
    parser.add_argument("--check-loaders",action="store_true",help="Also check forecasting windows and unified loaders (requires PyTorch)")
    parser.add_argument("--window-manifest",type=Path)
    args=parser.parse_args()
    report=validate_tree(args.datasets_root,args.dataset_size,args.radar_types)
    if args.check_loaders:
        report["loaders"]=validate_loaders(args.datasets_root,args.dataset_size,args.window_manifest,args.radar_types)
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2))


def validate_loaders(root: Path, size: str, manifest_path: Path | None, radar_types=RADAR_TYPES) -> dict:
    from foundation_models.common.dataset import (load_split, training_series,
        create_unified_pdw_dataloader, create_unified_multivariate_dataloader)
    from classic_methods.common import load_sequence_arrays, extract_window
    manifest=json.loads(manifest_path.read_text()) if manifest_path else None
    windows=0
    for mode in ("fixed","varying"):
        for kind in radar_types:
            for level in ERROR_LEVELS:
                folder=root/mode/kind/f"{size}_{level}"
                train=load_split(folder,"train","PRI",96,32)
                val=load_split(folder,"val","multivariate",96,32)
                require(len(training_series(train.windows))==len(train.windows),f"{folder}: lost training sequences")
                require(val.skipped_short==0,f"{folder}: short validation windows")
                target=None
                for length in (96,256,512,992):
                    loaded=load_split(folder,"test","multivariate",length,32,window_mode="tail")
                    require(loaded.skipped_short==0,f"{folder}: short test windows")
                    for window in loaded.windows:
                        require(window.context.shape==(5,length) and window.target.shape==(5,32),f"{folder}: window shape")
                        require(window.emitter_mask.all(),f"{folder}: unexpected masked targets")
                    current=np.stack([w.target for w in loaded.windows])
                    if target is not None:np.testing.assert_array_equal(target,current)
                    target=current
                    if manifest is not None:
                        random=load_split(folder,"test","PRI",length,32,window_mode="random",window_manifest=manifest)
                        for w in random.windows:
                            ctx,tgt,mask=load_sequence_arrays(folder/"test"/f"{w.sequence_id}.csv")
                            c,t,m=extract_window(ctx,tgt,mask,length,32,w.start)
                            # Classical arrays are float64; the model loader intentionally uses float32.
                            np.testing.assert_array_equal(w.context[0],c.astype(w.context.dtype))
                            np.testing.assert_array_equal(w.target[0],t.astype(w.target.dtype))
                            np.testing.assert_array_equal(w.emitter_mask,m)
                    windows+=len(loaded.windows)
        for factory in (create_unified_pdw_dataloader,create_unified_multivariate_dataloader):
            loader=factory(root/mode,profile_mode=mode,split="train",dataset_size=size,
                           radar_types=list(radar_types),max_seqs_per_dataset=1,context_len=96,horizon_len=32,batch_size=16,shuffle=False)
            conditions=len(radar_types)*len(ERROR_LEVELS)
            require(len(loader.dataset)==conditions,f"{mode}: unified loader missed a condition")
            batch=next(iter(loader))
            require(batch[0].shape[0]==min(16,conditions),f"{mode}: incomplete batch")
    return {"tail_windows_checked":windows,"same_tail_targets_across_lengths":True,
            "classical_and_foundation_random_windows_equal":manifest is not None,
            "unified_train_conditions_per_profile":len(radar_types)*len(ERROR_LEVELS),"model_weights_loaded":False}


if __name__=="__main__":main()
