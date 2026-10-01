import numpy as np
import pandas as pd
from typing import List, Optional

class Radar:
    def __init__(self, radar_id: str, freq_mean: float, freq_mode: str = "constant", freq_hopping_values: Optional[List[float]] = None):
        """
        Base Radar Class.
        """
        self.radar_id = radar_id
        self.freq_mean = freq_mean
        self.freq_mode = freq_mode
        self.freq_hopping_values = freq_hopping_values if freq_hopping_values else [freq_mean]

    def _generate_frequencies(self, num_pulses: int, freq_noise_std: float = 0.0) -> np.ndarray:
        if self.freq_mode == "constant":
            freqs = np.full(num_pulses, self.freq_mean)
        elif self.freq_mode == "hopping":
            cycles = np.tile(self.freq_hopping_values, int(np.ceil(num_pulses / len(self.freq_hopping_values))))
            freqs = cycles[:num_pulses]
        elif self.freq_mode == "agility":
            freqs = np.random.choice(self.freq_hopping_values, num_pulses)
        else:
            freqs = np.full(num_pulses, self.freq_mean)
        
        if freq_noise_std > 0:
            freqs += np.random.normal(0, freq_noise_std, num_pulses)
        
        return freqs

    def generate_pdws(self, duration: float, start_time: float = 0.0, toa_noise_std: float = 0.0, freq_noise_std: float = 0.0) -> pd.DataFrame:
        raise NotImplementedError("This method should be overridden by subclasses")

    def _finalize_df(self, toas: np.ndarray, pris: np.ndarray, duration: float, start_time: float, toa_noise_std: float, freq_noise_std: float) -> pd.DataFrame:
        # Filter by duration
        valid_idx = toas <= (start_time + duration)
        toas = toas[valid_idx]
        pris = pris[valid_idx]
        num_pulses = len(toas)
        
        if toa_noise_std > 0 and num_pulses > 0:
            toas += np.random.normal(0, toa_noise_std, num_pulses)
            # Re-calculate PRI based on noisy TOAs (ground truth PRI for this specific radar)
            pris = np.append([pris[0]], np.diff(toas))
            
        freqs = self._generate_frequencies(num_pulses, freq_noise_std)
        
        return pd.DataFrame({
            "Radar_ID": self.radar_id,
            "TOA": toas,
            "PRI": pris,
            "Frequency": freqs
        })


class StableRadar(Radar):
    def __init__(self, radar_id: str, pri: float, freq_mean: float, **kwargs):
        super().__init__(radar_id, freq_mean, **kwargs)
        self.pri = pri

    def generate_pdws(self, duration: float, start_time: float = 0.0, toa_noise_std: float = 0.0, freq_noise_std: float = 0.0) -> pd.DataFrame:
        num_pulses_est = int(np.ceil(duration / self.pri)) + 2
        pris = np.full(num_pulses_est, self.pri)
        toas = start_time + np.cumsum(pris) - self.pri
        return self._finalize_df(toas, pris, duration, start_time, toa_noise_std, freq_noise_std)


class JitterRadar(Radar):
    def __init__(self, radar_id: str, pri_mean: float, pri_jitter_std: float, freq_mean: float, **kwargs):
        super().__init__(radar_id, freq_mean, **kwargs)
        self.pri_mean = pri_mean
        self.pri_jitter_std = pri_jitter_std

    def generate_pdws(self, duration: float, start_time: float = 0.0, toa_noise_std: float = 0.0, freq_noise_std: float = 0.0) -> pd.DataFrame:
        num_pulses_est = int(np.ceil(duration / max(1.0, (self.pri_mean - self.pri_jitter_std*3)))) + 5
        pris = np.random.normal(self.pri_mean, self.pri_jitter_std, num_pulses_est)
        toas = start_time + np.cumsum(pris) - pris[0]
        return self._finalize_df(toas, pris, duration, start_time, toa_noise_std, freq_noise_std)


class StaggerRadar(Radar):
    def __init__(self, radar_id: str, stagger_pris: List[float], freq_mean: float, **kwargs):
        super().__init__(radar_id, freq_mean, **kwargs)
        self.stagger_pris = stagger_pris

    def generate_pdws(self, duration: float, start_time: float = 0.0, toa_noise_std: float = 0.0, freq_noise_std: float = 0.0) -> pd.DataFrame:
        avg_pri = np.mean(self.stagger_pris)
        num_pulses_est = int(np.ceil(duration / avg_pri)) + len(self.stagger_pris)
        cycles = np.tile(self.stagger_pris, int(np.ceil(num_pulses_est / len(self.stagger_pris))))
        pris = cycles[:num_pulses_est]
        toas = start_time + np.cumsum(pris) - pris[0]
        return self._finalize_df(toas, pris, duration, start_time, toa_noise_std, freq_noise_std)


class SlidingRadar(Radar):
    def __init__(self, radar_id: str, pri_start: float, pri_end: float, pulses_per_slide: int, freq_mean: float, **kwargs):
        super().__init__(radar_id, freq_mean, **kwargs)
        self.pri_start = pri_start
        self.pri_end = pri_end
        self.pulses_per_slide = pulses_per_slide

    def generate_pdws(self, duration: float, start_time: float = 0.0, toa_noise_std: float = 0.0, freq_noise_std: float = 0.0) -> pd.DataFrame:
        avg_pri = min(self.pri_start, self.pri_end)
        num_pulses_est = int(np.ceil(duration / avg_pri)) + self.pulses_per_slide
        slide_pattern = np.linspace(self.pri_start, self.pri_end, self.pulses_per_slide)
        cycles = np.tile(slide_pattern, int(np.ceil(num_pulses_est / self.pulses_per_slide)))
        pris = cycles[:num_pulses_est]
        toas = start_time + np.cumsum(pris) - pris[0]
        return self._finalize_df(toas, pris, duration, start_time, toa_noise_std, freq_noise_std)


class Environment:
    def __init__(self):
        self.radars = []

    def add_radar(self, radar: Radar):
        self.radars.append(radar)

    def generate(self, duration: float, start_time: float = 0.0, toa_noise_std: float = 0.0, freq_noise_std: float = 0.0) -> pd.DataFrame:
        """
        Generates and interleaves PDWs from all registered radars for a given time duration.
        """
        dfs = []
        for radar in self.radars:
            # Add random start offset to each radar (0 to 2000 microseconds)
            offset = np.random.uniform(0, 2000)
            df = radar.generate_pdws(
                duration=duration, 
                start_time=start_time + offset, 
                toa_noise_std=toa_noise_std, 
                freq_noise_std=freq_noise_std
            )
            dfs.append(df)
            
        if not dfs:
            return pd.DataFrame(columns=["Radar_ID", "TOA", "PRI", "Frequency"])
            
        interleaved_df = pd.concat(dfs, ignore_index=True)
        # Sort chronologically by TOA
        interleaved_df = interleaved_df.sort_values(by="TOA").reset_index(drop=True)
        
        # Calculate Delta-TOA (measured PRI between consecutive pulses from any radar)
        # This is what a real ESM sees before deinterleaving.
        interleaved_df["Measured_Delta_TOA"] = interleaved_df["TOA"].diff().fillna(0)
        
        return interleaved_df

