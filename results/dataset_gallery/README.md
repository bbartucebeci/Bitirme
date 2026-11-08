# Single-radar dataset gallery

These figures show 40 distinct test sequences from the 1000x128 datasets: one sequence for each combination of two profile modes, five radar types, and four error levels. Each radar type forms a column and each error level forms a row. The fixed and varying figures use different sequences, recorded in [selection.json](selection.json). No model prediction appears in these figures.

| Measurement | Fixed profile | Varying profile |
| --- | --- | --- |
| PRI | [View figure](fixed_pri.png) | [View figure](varying_pri.png) |
| Frequency | [View figure](fixed_frequency.png) | [View figure](varying_frequency.png) |
| Pulse width | [View figure](fixed_pw.png) | [View figure](varying_pw.png) |
| Amplitude | [View figure](fixed_amplitude.png) | [View figure](varying_amplitude.png) |
| Angle of arrival | [View figure](fixed_aoa.png) | [View figure](varying_aoa.png) |

The horizontal axis is the position among 128 observed pulses. The initial timing anchor is excluded when present. In the PRI figures, the blue line is the interval between adjacent observed pulses (`Measured_Delta_TOA`); the orange dashed line is the generator's source `PRI` for genuine emitter pulses. These can differ when pulses are missing or extra pulses appear. For the other measurements, the blue line shows the recorded CSV value. A red cross marks a pulse whose `Radar_ID` is not `R_SINGLE`. Every panel has its own vertical scale, so compare patterns and read the axis values before comparing magnitudes.

The generated CSV files remain local. To reproduce the figures from the repository root after generating the 1000x128 datasets, run:

```powershell
python -m dataset_generator.plot_sequence_gallery
```

The selection is deterministic: it uses `seq_0800` through `seq_0839`, with one sequence assigned to each dataset condition. The command writes these ten PNGs and refreshes `selection.json` in this folder.
