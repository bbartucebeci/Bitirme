# Stagger source-level separation update

Updated on `long-seq-1024` to keep every pair of neighboring sorted source PRI
levels more than 10 µs apart. Clock/measurement effects and observed gaps after
losses are outside this source-level constraint.

- Fixed: 32 levels L[j] = 750 + 500j/31 µs, j=0,…,31. The existing permutation,
  random phase and cycle mean 1000 µs are retained. Sorted spacing is
  500/31 = 16.129032 µs.
- Varying: s ~ Uniform(0.24,0.30), with the existing μ ~ Uniform(800,1200),
  K uniform over {16,…,32}, equal spacing and sampled permutation.
  Spacing = 2μs/(K−1), at least 384/31 = 12.387097 µs.
- The profile validator rejects spacing <=10 µs before simulation. No resampling
  or post-generation recentering is introduced.
- This does not require disjoint ±10 µs scoring corridors.

## Verification

All 12 source/profile/generation tests and all 5 existing window tests pass.
The added test covers μ/s/K boundary combinations, fixed spacing, rejection of
exactly 10 µs and smaller gaps. The 1000-profile varying test checks the new span
range and source separation for every sampled stagger profile.

Fresh stagger-only smoke generation covers both profiles and all eight error
levels: 16 datasets × 10 captures = 160 captures / 164,000 PDW rows. Each capture
contains 1024 observed intervals plus one anchor. Split totals are 112 train,
16 validation and 32 test captures. All CSV/schema/seed/profile checks pass.
The fresh manifest and loader audit verify 128 windows, identical classical/model
random windows after float32 conversion, and common last-32 targets for
L=96/256/512/992. No model weights were loaded.

Data: `datasets/complex_pri_stagger_spacing_smoke/`.
Audit: `datasets/complex_pri_stagger_spacing_smoke_validation.json`.
The Excel fixed/varying stagger definitions were updated to match; the previously
approved four-state Markov definition and all unrelated cells were preserved.
No full production generation, model training, commit or push was performed.
