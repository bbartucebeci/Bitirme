# Four-state Markov agile update

Updated only the Markov source law, its fixed/varying configuration and directly
related tests/documentation on `long-seq-1024`. Other radar laws and error levels
are unchanged by this update.

Fixed A–D levels: 850, 950, 1050, 1150 µs.
Varying A–D levels: μ × [1−s, 1−s/3, 1+s/3, 1+s], with the existing
μ ~ Uniform(800,1200) and s ~ Uniform(0.12,0.18).

| Current / next | A | B | C | D |
|---|---:|---:|---:|---:|
| A | 0.10 | 0.70 | 0.10 | 0.10 |
| B | 0.10 | 0.10 | 0.70 | 0.10 |
| C | 0.10 | 0.10 | 0.10 | 0.70 |
| D | 0.70 | 0.10 | 0.10 | 0.10 |

Initial state is uniform over the four states. Both row and column sums must be
one, giving uniform stationary occupancy and expected PRI 1000 µs or μ. Finite
captures are not recentered. State transitions use the current row of the matrix;
source prefixes remain reproducible when capture duration is extended. Source
state advances before receiver losses, as before.

## Checks completed

- All 11 source/profile/generation tests pass, including all 16 conditional
  transition frequencies over 200,000 source events, stationary occupancy,
  four-level varying construction, retry prefix equality and malformed matrix
  rejection (including row-stochastic but non-doubly-stochastic matrices).
- All 5 existing window-protocol tests pass.
- Fresh Markov-only smoke generation: 2 profiles × 8 error levels × 10 captures
  = 16 datasets, 160 captures, 164,000 PDW rows.
- Split totals: 112 train, 16 validation, 32 test captures.
- Every per-sequence and combined CSV passes the dataset audit.
- Fresh manifest contains 128 windows. Loader checks verify identical classical
  and model windows (after existing float32 conversion), identical tail targets
  across four context lengths, and all eight conditions in each unified loader.

Smoke data: `datasets/complex_pri_markov4_smoke/`.
Audit: `datasets/complex_pri_markov4_smoke_validation.json`.
The validator now accepts `--radar-types markov_agile` to audit this subset;
omitting it still audits all eight radar types.

Old five-state smoke data remain historical and were not overwritten. No full
dataset generation or model training was run. No commit or push was made.
