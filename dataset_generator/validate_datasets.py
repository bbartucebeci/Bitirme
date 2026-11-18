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
from dataset_generator.sequence_io import SCHEMA_V2, SOURCE_COLUMNS, read_sequence_frame, is_boundary_dataset


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_source_storage(raw, frame, metadata, record, path):
    require(list(raw.columns)==OUTPUT_COLUMNS+SOURCE_COLUMNS,f"{path}: source schema mismatch")
    require(len(raw)==int(record.source_rows),f"{path}: source row count mismatch")
    np.testing.assert_array_equal(raw.source_pulse_id,np.arange(len(raw)))
    for field in ("poi_keep","global_keep","observed_keep"):
        require(raw[field].dtype==bool,f"{path}: {field} is not boolean")
    np.testing.assert_array_equal(raw.observed_keep,raw.poi_keep & raw.global_keep)
    require(int(record.loss_seed)==zlib.crc32(f"{int(record.sequence_seed)}|loss_v2".encode()),f"{path}: loss seed mismatch")
    draws=np.random.default_rng(int(record.loss_seed)).random((len(raw),2))
    np.testing.assert_array_equal(raw.poi_keep,draws[:,0]<metadata["error_parameters"]["poi"])
    np.testing.assert_array_equal(raw.global_keep,draws[:,1]>=metadata["error_parameters"]["global_drop_rate"])
    context=int(metadata["context_intervals"]);horizon=int(metadata["max_horizon"])
    observed=np.flatnonzero(raw.observed_keep.to_numpy())[:context+1]
    require(len(observed)==context+1,f"{path}: short observed context")
    boundary=int(observed[-1])
    ids=np.r_[observed,np.arange(boundary+1,boundary+horizon+1)]
    np.testing.assert_array_equal(frame.source_pulse_id,ids)
    expected_indices=np.full(len(raw),-1,dtype=int);expected_indices[ids]=np.arange(len(ids))
    np.testing.assert_array_equal(raw.sequence_index,expected_indices)
    np.testing.assert_array_equal(raw.pulse_index,expected_indices)
    expected_segments=np.full(len(raw),"missed_context",dtype=object)
    expected_segments[observed]="context";expected_segments[observed[0]]="anchor"
    expected_segments[boundary+1:]="horizon"
    np.testing.assert_array_equal(raw.segment,expected_segments)
    require(len(raw)==boundary+horizon+1,f"{path}: unexpected source suffix")
    numeric=raw[["TOA","PRI","Frequency","PW","Amplitude","AOA","Measured_Delta_TOA"]]
    require(np.isfinite(numeric.to_numpy()).all() and (np.diff(raw.TOA)>0).all(),f"{path}: invalid complete PDW stream")
    require((raw.PRI>0).all() and (raw.PW>0).all() and raw.AOA.between(0,360,inclusive="left").all(),f"{path}: invalid source PDW ranges")
    future=frame.iloc[context+1:]
    require(len(future)==horizon and (np.diff(future.source_pulse_id)==1).all(),f"{path}: non-consecutive future")
    return int((~future.observed_keep).sum())


def validate_tree(root: Path, dataset_size: str, radar_types=RADAR_TYPES) -> dict:
    count, intervals = map(int, dataset_size.split("x"))
    collection_path=root.parent/"collection.json"
    if collection_path.is_file():
        collection=json.loads(collection_path.read_text(encoding="utf-8"))
        require(collection.get("status")=="complete","Dataset collection generation is incomplete")
        require(collection.get("dataset_size")==dataset_size,"Collection dataset size mismatch")
        require(len(collection["completed_conditions"])==len(set(collection["completed_conditions"]))==collection["expected_conditions"],"Collection condition inventory mismatch")
        condition_keys={f"{p}/{r}/{e}" for p in collection["profiles"] for r in collection["radar_types"] for e in collection["error_levels"]}
        require(set(collection["completed_conditions"])==condition_keys,"Collection condition names mismatch")
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
    restored=0
    schemas=set()
    for mode in ("fixed","varying"):
        for kind in radar_types:
            reference_profiles = None
            for level in ERROR_LEVELS:
                folder = root/mode/kind/f"{dataset_size}_{level}"
                m=yaml.safe_load((folder/"metadata.yaml").read_text(encoding="utf-8"))
                require(m["schema_version"] in ("complex_pri_v1",SCHEMA_V2),f"{folder}: wrong schema")
                schemas.add(m["schema_version"])
                v2=is_boundary_dataset(m)
                if v2:
                    require(m["context_intervals"]+m["max_horizon"]==intervals,f"{folder}: context/horizon size mismatch")
                    require(m["target_policy"]=="consecutive_source_pulses" and m["window_mode"]=="boundary",f"{folder}: target policy mismatch")
                require((m["radar_type"],m["profile_mode"],m["error_level"])==(kind,mode,level),f"{folder}: identity mismatch")
                require(m["sequence_count"]==count and m["expected_pulses_per_sequence"]==intervals,f"{folder}: size mismatch")
                rows_field="model_rows_per_sequence" if v2 else "observed_rows_per_sequence"
                require(m[rows_field]==intervals+1 and m["first_row_is_anchor"],f"{folder}: anchor metadata mismatch")
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
                    combined_path=folder/split/"sequences.csv"
                    if m.get("storage_layout") in ("per_sequence_csv","source_stream_per_sequence"):
                        require(not combined_path.exists(),f"{folder}/{split}: duplicate combined storage")
                    combined=pd.read_csv(combined_path) if combined_path.is_file() else None
                    if combined is not None:require(len(combined)==n*(intervals+1),f"{folder}/{split}: combined length mismatch")
                    for i,p in enumerate(files):
                        record=records.loc[p.stem]
                        frame=read_sequence_frame(p)
                        if v2:
                            restored+=validate_source_storage(pd.read_csv(p),frame,m,record,p)
                        else:require(list(frame.columns)==OUTPUT_COLUMNS,f"{p}: unexpected schema")
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
                        if combined is not None:pd.testing.assert_frame_equal(frame,combined.iloc[i*(intervals+1):(i+1)*(intervals+1)].reset_index(drop=True))
                        key=f"{m['seed']}|{kind}|{mode}|{level}|{intervals}|{p.stem}"
                        require(int(record.sequence_seed)==zlib.crc32(key.encode()),f"{p}: seed mismatch")
                        init=json.loads(record.initialization_json)
                        if init:phases[kind].add(json.dumps(init,sort_keys=True))
                        summary["sequences"]+=1;summary["rows"]+=len(frame)
                    summary["split_sequences"][split]+=n
                bytes_total+=sum(p.stat().st_size for p in folder.rglob("*") if p.is_file())
                summary["datasets"]+=1
                print(f"[VALIDATED] {mode}/{kind}/{level}",flush=True)
    summary["bytes_on_disk"]=bytes_total
    require(len(schemas)==1,"Mixed dataset protocols in one collection")
    summary["schema_version"]=next(iter(schemas))
    summary["restored_horizon_pulses"]=restored
    summary["checks"][2]="per-sequence storage; compare combined CSV only for historical datasets"
    if SCHEMA_V2 in schemas:
        summary["checks"].extend(["complete source rows stored once", "seeded POI/global whole-row masks",
                                  "context and horizon source IDs", "consecutive-source future including restored PDWs"])
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
                metadata=yaml.safe_load((folder/"metadata.yaml").read_text(encoding="utf-8"))
                v2=is_boundary_dataset(metadata)
                window_mode="boundary" if v2 else "tail"
                train=load_split(folder,"train","PRI",96,32,window_mode=window_mode)
                val=load_split(folder,"val","multivariate",96,32,window_mode=window_mode)
                require(len(training_series(train.windows))==len(train.windows),f"{folder}: lost training sequences")
                require(val.skipped_short==0,f"{folder}: short validation windows")
                target=None
                for length in ((96,128,256,512,992,1024) if v2 else (96,256,512,992)):
                    loaded=load_split(folder,"test","multivariate",length,32,window_mode=window_mode)
                    require(loaded.skipped_short==0,f"{folder}: short test windows")
                    for window in loaded.windows:
                        require(window.context.shape==(5,length) and window.target.shape==(5,32),f"{folder}: window shape")
                        require(window.emitter_mask.all(),f"{folder}: unexpected masked targets")
                    current=np.stack([w.target for w in loaded.windows])
                    if target is not None:np.testing.assert_array_equal(target,current)
                    target=current
                    if v2:
                        shorter=load_split(folder,"test","multivariate",length,16,window_mode="boundary")
                        np.testing.assert_array_equal(np.stack([w.target for w in shorter.windows]),current[:,:,:16])
                        for w in loaded.windows:
                            ctx,tgt,mask=load_sequence_arrays(folder/"test"/f"{w.sequence_id}.csv")
                            c,t,m=extract_window(ctx,tgt,mask,length,32,w.start)
                            np.testing.assert_array_equal(w.context[0],c.astype(w.context.dtype))
                            np.testing.assert_array_equal(w.target[0],t.astype(w.target.dtype))
                    if manifest is not None:
                        random=load_split(folder,"test","PRI",length,32,window_mode=window_mode if v2 else "random",window_manifest=manifest)
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
    return {"forecast_windows_checked":windows,"same_targets_across_context_lengths":True,
            "boundary_target_prefixes_checked":v2,
            "classical_and_foundation_manifest_windows_equal":manifest is not None,
            "classical_and_foundation_boundary_windows_equal":v2,
            "unified_train_conditions_per_profile":len(radar_types)*len(ERROR_LEVELS),"model_weights_loaded":False}


if __name__=="__main__":main()
