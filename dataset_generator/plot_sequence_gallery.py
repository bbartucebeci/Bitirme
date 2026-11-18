"""Read-only galleries: one radar/profile/channel per figure, all selected error levels."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator
import numpy as np
import pandas as pd
import yaml

from dataset_generator.catalog import RADAR_TYPES, ERROR_LEVELS, PROJECT_ROOT, family_for_schema
from dataset_generator.sequence_io import read_sequence_frame

PROFILES = ("fixed", "varying")
CHANNELS = (
    ("PRI", "Measured_Delta_TOA", "Interval (µs)"),
    ("Frequency", "Frequency", "Frequency (MHz)"),
    ("PW", "PW", "Pulse width (µs)"),
    ("Amplitude", "Amplitude", "Amplitude (dBm)"),
    ("AOA", "AOA", "AOA (degrees)"),
)
MIN_AXIS_SPAN = {"PRI":10., "Frequency":2., "PW":.05, "Amplitude":1., "AOA":2.}


def load_sequence(path: Path, pulse_count: int, start: int = 0) -> pd.DataFrame:
    if pulse_count <= 0 or start < 0:
        raise ValueError("Pulse count must be positive and start nonnegative")
    frame = read_sequence_frame(path).sort_values("pulse_index").reset_index(drop=True)
    required = {"Radar_ID", "PRI", "Measured_Delta_TOA", "pulse_index", *(item[1] for item in CHANNELS)}
    if required - set(frame.columns):
        raise ValueError(f"{path}: missing columns {sorted(required-set(frame.columns))}")
    # Match forecasting loaders at any length, including 1025-row captures.
    if len(frame)>1 and float(frame.loc[0,"Measured_Delta_TOA"])==0.:
        frame=frame.iloc[1:].reset_index(drop=True)
    if len(frame)<start+pulse_count:
        raise ValueError(f"{path}: requested [{start}:{start+pulse_count}], only {len(frame)} intervals after anchor removal")
    frame=frame.iloc[start:start+pulse_count].copy()
    if not np.isfinite(frame[["PRI",*(item[1] for item in CHANNELS)]].to_numpy(dtype=float)).all():
        raise ValueError(f"{path}: non-finite plot values")
    return frame


def plot_profile(profile,radar,channel,value_column,unit_label,selected,levels,output_dir,dpi):
    columns=min(4,len(levels)); rows=(len(levels)+columns-1)//columns
    fig,axes=plt.subplots(rows,columns,figsize=(4.8*columns,3.6*rows),sharex=True,squeeze=False)
    has_non_emitter=False
    for axis,level in zip(axes.flat,levels):
        sequence_id,frame=selected[(profile,radar,level)]
        x=frame.pulse_index.to_numpy(); genuine=frame.Radar_ID.eq("R_SINGLE").to_numpy()
        values=frame[value_column].to_numpy(dtype=float)
        axis.plot(x,values,color="#1775a5",linewidth=1.,marker=".",markersize=1.8)
        if "segment" in frame and frame.segment.eq("horizon").any():
            boundary=float(frame.loc[frame.segment.eq("horizon"),"pulse_index"].iloc[0])-.5
            axis.axvline(boundary,color="#222222",linestyle=":",linewidth=1.)
        bounds=values
        if channel=="PRI":
            source=frame.PRI.to_numpy(dtype=float)
            axis.plot(x,np.where(genuine,source,np.nan),color="#e27929",linewidth=1.1,linestyle="--")
            bounds=np.r_[values,source[genuine]]
        if (~genuine).any():
            has_non_emitter=True
            axis.scatter(x[~genuine],values[~genuine],color="#b51f37",marker="x",s=18,zorder=3)
        lower,upper=float(np.min(bounds)),float(np.max(bounds))
        if upper-lower<MIN_AXIS_SPAN[channel]:
            center=(lower+upper)/2; half=MIN_AXIS_SPAN[channel]/2
            axis.set_ylim(center-half,center+half)
        axis.ticklabel_format(axis="y",style="plain",useOffset=False)
        axis.yaxis.set_major_locator(MaxNLocator(nbins=5))
        axis.set_title(f"{level} · {sequence_id}",fontsize=11)
        axis.set_xlabel("Selected pulse index; dotted line starts consecutive future" if "segment" in frame else "Observed pulse index (anchor excluded)",fontsize=9)
        axis.set_ylabel(unit_label,fontsize=9)
        axis.grid(alpha=.18); axis.tick_params(labelsize=8)
    for axis in list(axes.flat)[len(levels):]:axis.set_visible(False)
    observed="Observed ΔTOA" if channel=="PRI" else f"Recorded {channel}"
    handles=[Line2D([0],[0],color="#1775a5",label=observed)]
    if channel=="PRI":handles.append(Line2D([0],[0],color="#e27929",linestyle="--",label="Source PRI at retained pulses"))
    if has_non_emitter:handles.append(Line2D([0],[0],color="#b51f37",marker="x",linestyle="None",label="Non-emitter pulse"))
    family=frame.attrs.get("dataset_family","old_complex_pri")
    fig.suptitle(f"{family} · {radar.replace('_',' ')} · {profile} profile · {channel}",fontsize=16,y=.99)
    fig.legend(handles=handles,loc="upper center",bbox_to_anchor=(.5,.95),ncol=len(handles),frameon=False)
    fig.text(.5,.895,"Each error-level panel has its own vertical scale.",ha="center",fontsize=9)
    fig.tight_layout(rect=(0,0,1,.855))
    destination=output_dir/radar/f"{family}_{profile}_{channel.lower()}.png"
    destination.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(destination,dpi=dpi); plt.close(fig)
    return destination


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--datasets-root",type=Path,required=True,help="Directory containing fixed/ and varying/")
    parser.add_argument("--dataset-size",default="1000x1024")
    parser.add_argument("--profiles",nargs="+",choices=PROFILES,default=PROFILES)
    parser.add_argument("--radar-types",nargs="+",choices=RADAR_TYPES,default=RADAR_TYPES)
    parser.add_argument("--error-levels",nargs="+",choices=ERROR_LEVELS,default=ERROR_LEVELS)
    parser.add_argument("--channels",nargs="+",choices=[item[0] for item in CHANNELS],default=[item[0] for item in CHANNELS])
    parser.add_argument("--first-test-id",type=int,help="Same sequence ID in every condition; default: first test ID from metadata")
    parser.add_argument("--pulses",type=int,default=1024)
    parser.add_argument("--start",type=int,default=0,help="Zero-based start after dropping the anchor")
    parser.add_argument("--dpi",type=int,default=160)
    parser.add_argument("--output-dir",type=Path,help="Default: results/dataset_gallery/<dataset_family>; requires an empty directory")
    args=parser.parse_args()
    if args.first_test_id is not None and args.first_test_id<0:parser.error("Test ID must be nonnegative")
    if args.pulses<=0 or args.start<0 or args.dpi<=0:parser.error("Pulses/dpi must be positive; start nonnegative")
    first_metadata=args.datasets_root/args.profiles[0]/args.radar_types[0]/f"{args.dataset_size}_{args.error_levels[0]}"/"metadata.yaml"
    first_schema=yaml.safe_load(first_metadata.read_text(encoding="utf-8")).get("schema_version","complex_pri_v1")
    family=family_for_schema(first_schema)
    if args.output_dir is None:args.output_dir=PROJECT_ROOT/"results"/"dataset_gallery"/family
    if args.output_dir.exists() and any(args.output_dir.iterdir()):parser.error(f"Output directory is not empty: {args.output_dir}")
    selected,manifest={},[]
    # Validate all inputs before creating output; never invoke dataset generation.
    for profile in args.profiles:
        for radar in args.radar_types:
            for level in args.error_levels:
                folder=args.datasets_root/profile/radar/f"{args.dataset_size}_{level}"
                with (folder/"metadata.yaml").open(encoding="utf-8") as handle:metadata=yaml.safe_load(handle)
                first=metadata["split"]["train"]["sequence_count"]+metadata["split"]["val"]["sequence_count"]
                sid=args.first_test_id if args.first_test_id is not None else first
                if not first<=sid<first+metadata["split"]["test"]["sequence_count"]:raise ValueError(f"{folder}: seq_{sid:04d} is not in the test split")
                if (metadata["radar_type"],metadata["profile_mode"],metadata["error_level"])!=(radar,profile,level):raise ValueError(f"{folder}: metadata identity mismatch")
                if family_for_schema(metadata.get("schema_version","complex_pri_v1"))!=family:raise ValueError("Cannot mix dataset families in one gallery")
                if args.start+args.pulses>metadata["expected_pulses_per_sequence"]:raise ValueError(f"{folder}: window exceeds metadata length")
                sequence_id=f"seq_{sid:04d}"; path=folder/"test"/f"{sequence_id}.csv"
                frame=load_sequence(path,args.pulses,args.start)
                frame.attrs["dataset_family"]=family
                selected[(profile,radar,level)]=(sequence_id,frame)
                manifest.append({"profile":profile,"radar_type":radar,"error_level":level,"sequence_id":sequence_id,
                                 "dataset_family":family,"source_csv":str(path.resolve()),"start_after_anchor":args.start,"plotted_intervals":len(frame)})
    args.output_dir.mkdir(parents=True,exist_ok=True)
    count=0
    for profile in args.profiles:
        for radar in args.radar_types:
            for channel,column,unit in CHANNELS:
                if channel in args.channels:
                    path=plot_profile(profile,radar,channel,column,unit,selected,tuple(args.error_levels),args.output_dir,args.dpi)
                    count+=1; print(f"[SAVED] {path}")
    (args.output_dir/"selection.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    links=[f"| {radar} | "+", ".join(f"[{profile} {channel}]({radar}/{family}_{profile}_{channel.lower()}.png)" for profile in args.profiles for channel,_,_ in CHANNELS if channel in args.channels)+" |" for radar in args.radar_types]
    text=[f"# {family}: dataset gallery","",f"Dataset size: {args.dataset_size}. Start after anchor: {args.start}. Plotted intervals: {args.pulses}.",
          "These are dataset observations and source values, not model forecasts.",
          "The dotted line, when present, starts the consecutive-source future.","",
          "| Radar | Figures |","|---|---|",*links,"",
          "Each figure contains the selected error levels. Additional channel figures are in each radar directory.",""]
    (args.output_dir/"README.md").write_text("\n".join(text),encoding="utf-8")
    print(f"[DONE] {count} figures from {len(manifest)} selected captures; input CSVs unchanged")


if __name__=="__main__":main()
