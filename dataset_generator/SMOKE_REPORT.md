# Complex PRI implementation and smoke results

The results below describe the initial five-state Markov implementation.
The later four-state Markov update and its separate smoke checks are documented
in `MARKOV_SMOKE_REPORT.md`. Old smoke captures are retained as historical data.
The subsequent stagger spacing update is covered in `STAGGER_SMOKE_REPORT.md`;
the original stagger captures below use the earlier, narrower spacing.

Work was performed only on `long-seq-1024`, after fast-forwarding to
`f828052d87631de8f143ea5f504e24783e1d1759`. Changes remain in the working tree.
No full dataset generation, model training, model download, commit or push was run.

## Implemented

- Eight source laws and the finalized fixed/varying parameters in the YAML configs.
- Five-level D&S, 16–32-level varying / 32-level fixed stagger without added PRI
  jitter, separate sinusoidal / triangular / Markov source classes, random source
  initialization recorded once per sequence.
- Eight error levels with zero false pulse rate and zero multipath. Existing POI,
  global drop, measurement noise, AOA drift and receiver stages retained.
- Separate output root, overwrite protection, unchanged 12-column PDW schema,
  profile/seed/initialization records, and the existing train/val/test split.
- Shared condition catalog and explicit dataset root/size selection in the model
  data paths. Fine-tuning still pools conditions; loss/model algorithms are unchanged.
- Fresh SHA256/window manifests; classical runner checks hashes when available.
  New classical summaries keep radar types and error levels separate.

## Verified results

| Check | Result |
|---|---|
| Source/profile/generation tests | 11 passed |
| Existing Chronos window-protocol tests | 5 passed |
| Smoke condition matrix | 2 profiles × 8 laws × 8 levels = 128 datasets |
| Captures per condition | 10, each with 1024 observed intervals plus one anchor |
| Main smoke total | 1280 captures; 1,312,000 PDW rows |
| Split totals | 896 train / 128 validation / 256 test captures |
| CSV audit | Every capture and combined split checked; no noise/echo labels |
| Source losses | Retained PRI indices and accumulated TOA gaps verified with isolated losses |
| Model/classical window alignment | 1024 manifest entries identical between both builders |
| Tail-target alignment | 1024 test windows checked across L=96/256/512/992 |
| Unified loaders | Both uni/multivariate paths include all 64 conditions per profile |
| Chronos coverage CLI | All 64 varying conditions have 2 complete 992+32 test windows |
| TiRex coverage CLI | Both profiles: all 128 conditions have 2 complete 992+32 windows |
| Kalman runner smoke | 64 jobs / 128 forecasts; every forecast has 32 valid targets, no shortened contexts |
| Independent CLI repeat | All 16 files of varying Markov / Level 7 match byte-for-byte |
| Existing receiver regression | Original and modified five-radar scenario yield 980 exactly identical PDW rows at default phase |
| Existing data | Original 40 dataset folders retained; production `datasets/complex_pri_v1` absent |

The CSV audit checks exact split IDs, row counts, finite values, positive PRI/PW,
strict TOA order, Delta-TOA equality, metadata, generation seeds, profile ranges and
profile identity across levels. The loader audit additionally checks array shapes,
target masks, complete training/validation windows and identical tail targets.
Classical float64 arrays are compared with the existing float32 model conversion.

Smoke captures and logs are under `datasets/complex_pri_v1_smoke/` and
`datasets/complex_pri_v1_smoke_*.log`. The complete JSON audit is
`datasets/complex_pri_v1_smoke_validation.json`. Per-radar Kalman results are under
`datasets/complex_pri_v1_smoke/classic_smoke/by_radar/`. A visual inspection gallery
is `datasets/complex_pri_v1_smoke/fixed_clean_gallery.png`.

## Environment limits

Exponential Smoothing could not import its existing statsmodels compiled DLL:
Windows Application Control blocked `_conventional`. No environment/security
settings or algorithms were changed. The same runner was exercised successfully
with the existing NumPy Kalman implementation instead.

The current Chronos environment does not have TimesFM installed. Consequently
TimesFM entry points and t0-gamma's covariate entry point (which already imports
TimesFM) were syntax-checked, but their runtime imports/inference were not verified.
Seven other model entry points passed CLI import/help checks. No foundation-model
weights were loaded. These smoke forecasts are execution checks, not an accuracy
benchmark or evidence that a model benefits from the new source laws.
