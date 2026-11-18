# Complex PRI dataset gallery (1024 intervals)

These 80 PNGs show the completed eight-law benchmark: fixed and varying profiles,
all eight error levels, and five PDW parameters. Each figure contains eight panels
for the same radar/profile/channel. Every panel uses `seq_0800` from its test split
and shows all 1024 observed intervals after removal of the timing anchor.

| Radar type | Fixed PRI | Varying PRI |
|---|---|---|
| Stable | [View](stable/fixed_pri.png) | [View](stable/varying_pri.png) |
| Gaussian jitter | [View](jitter/fixed_pri.png) | [View](jitter/varying_pri.png) |
| Many-level stagger | [View](stagger/fixed_pri.png) | [View](stagger/varying_pri.png) |
| Many-level D&S | [View](dwell_and_switch/fixed_pri.png) | [View](dwell_and_switch/varying_pri.png) |
| Sliding | [View](sliding/fixed_pri.png) | [View](sliding/varying_pri.png) |
| Sinusoidal | [View](sinusoidal/fixed_pri.png) | [View](sinusoidal/varying_pri.png) |
| Triangular sliding | [View](triangular_sliding/fixed_pri.png) | [View](triangular_sliding/varying_pri.png) |
| Markov agile | [View](markov_agile/fixed_pri.png) | [View](markov_agile/varying_pri.png) |

Each radar directory also contains `fixed_` and `varying_` figures for `frequency`,
`pw`, `amplitude` and `aoa`. Panels use independent vertical scales. In PRI figures,
blue is observed Delta-TOA and dashed orange is source PRI at retained pulses;
missing pulses may make observed spacing larger than source PRI.

Current source definitions include 32 fixed stagger levels from 750 to 1250 µs
(varying span fraction 0.24–0.30) and four-state Markov PRI with 850/950/1050/1150 µs
fixed levels. Markov forward cyclic transitions have probability 0.70; each other
transition has probability 0.10. False pulse and multipath rates are zero.

The local production audit completed on 18 November 2026: 128 datasets,
128,000 sequences and 131,200,000 stored PDW rows. Every dataset has 700 training,
100 validation and 200 test captures; every capture has 1024 intervals plus an
anchor. Only the PNGs are published here. Raw/combined CSVs, profile records,
generation records and the local validation report are not included.

Source run: `complex_pri_full_20261117_230416`, gallery `gallery_20261118_101548`.
See [generation and validation instructions](../../../dataset_generator/README.md).

To regenerate a gallery after production (from the repository root):

```powershell
python -B -m dataset_generator.plot_sequence_gallery --datasets-root <production-root>/single_radar --dataset-size 1000x1024 --first-test-id 800 --pulses 1024 --output-dir <new-gallery-directory>
```

The plotter only reads dataset files and refuses a nonempty gallery destination.
