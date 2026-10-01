import numpy as np
import pandas as pd
from typing import List, Optional

class Radar:
    def __init__(self, radar_id: str, freq_mean: float, freq_mode: str = "constant", freq_hopping_values: Optional[List[float]] = None):
        """
        Base Radar Class.
        :param radar_id: Identifier for the radar
        :param freq_mean: Base frequency in MHz
        :param freq_mode: "constant", "hopping", or "agility"
        :param freq_hopping_values: List of frequencies for hopping/agility mode
        """
        self.radar_id = radar_id
        self.freq_mean = freq_mean
        self.freq_mode = freq_mode
        self.freq_hopping_values = freq_hopping_values if freq_hopping_values else [freq_mean]

    def _generate_frequencies(self, num_pulses: int, freq_noise_std: float = 0.0) -> np.ndarray:
        if self.freq_mode == "constant":
            freqs = np.full(num_pulses, self.freq_mean)
        elif self.freq_mode == "hopping":
            # Cycle through hopping values sequentially
            cycles = np.tile(self.freq_hopping_values, int(np.ceil(num_pulses / len(self.freq_hopping_values))))
            freqs = cycles[:num_pulses]
        elif self.freq_mode == "agility":
            # Randomly select from hopping values
            freqs = np.random.choice(self.freq_hopping_values, num_pulses)
        else:
            freqs = np.full(num_pulses, self.freq_mean)
        
        # Add measurement noise
        if freq_noise_std > 0:
            freqs += np.random.normal(0, freq_noise_std, num_pulses)
        
        return freqs

    def generate_pdws(self, num_pulses: int, start_time: float = 0.0, toa_noise_std: float = 0.0, freq_noise_std: float = 0.0) -> pd.DataFrame:
        """
        Generates PDWs for the radar. Must be implemented by subclasses.
        """
        raise NotImplementedError("This method should be overridden by subclasses")

class StableRadar(Radar):
    def __init__(self, radar_id: str, pri: float, freq_mean: float, **kwargs):
        super().__init__(radar_id, freq_mean, **kwargs)
        self.pri = pri

    def generate_pdws(self, num_pulses: int, start_time: float = 0.0, toa_noise_std: float = 0.0, freq_noise_std: float = 0.0) -> pd.DataFrame:
        pris = np.full(num_pulses, self.pri)
        toas = start_time + np.cumsum(pris) - self.pri
        
        if toa_noise_std > 0:
            toas += np.random.normal(0, toa_noise_std, num_pulses)
            # Re-calculate PRI based on noisy TOAs (as a real ESM would measure)
            pris = np.append([self.pri], np.diff(toas))
            
        freqs = self._generate_frequencies(num_pulses, freq_noise_std)
        
        df = pd.DataFrame({
            "Radar_ID": self.radar_id,
            "TOA": toas,
            "PRI": pris,
            "Frequency": freqs
        })
        return df

class JitterRadar(Radar):
    def __init__(self, radar_id: str, pri_mean: float, pri_jitter_std: float, freq_mean: float, **kwargs):
        super().__init__(radar_id, freq_mean, **kwargs)
        self.pri_mean = pri_mean
        self.pri_jitter_std = pri_jitter_std

    def generate_pdws(self, num_pulses: int, start_time: float = 0.0, toa_noise_std: float = 0.0, freq_noise_std: float = 0.0) -> pd.DataFrame:
        pris = np.random.normal(self.pri_mean, self.pri_jitter_std, num_pulses)
        toas = start_time + np.cumsum(pris) - pris[0] # start at start_time
        
        if toa_noise_std > 0:
            toas += np.random.normal(0, toa_noise_std, num_pulses)
            pris = np.append([pris[0]], np.diff(toas))
            
        freqs = self._generate_frequencies(num_pulses, freq_noise_std)
        
        df = pd.DataFrame({
            "Radar_ID": self.radar_id,
            "TOA": toas,
            "PRI": pris,
            "Frequency": freqs
        })
        return df

class StaggerRadar(Radar):
    def __init__(self, radar_id: str, stagger_pris: List[float], freq_mean: float, **kwargs):
        super().__init__(radar_id, freq_mean, **kwargs)
        self.stagger_pris = stagger_pris

    def generate_pdws(self, num_pulses: int, start_time: float = 0.0, toa_noise_std: float = 0.0, freq_noise_std: float = 0.0) -> pd.DataFrame:
        cycles = np.tile(self.stagger_pris, int(np.ceil(num_pulses / len(self.stagger_pris))))
        pris = cycles[:num_pulses]
        toas = start_time + np.cumsum(pris) - pris[0]
        
        if toa_noise_std > 0:
            toas += np.random.normal(0, toa_noise_std, num_pulses)
            pris = np.append([pris[0]], np.diff(toas))
            
        freqs = self._generate_frequencies(num_pulses, freq_noise_std)
        
        df = pd.DataFrame({
            "Radar_ID": self.radar_id,
            "TOA": toas,
            "PRI": pris,
            "Frequency": freqs
        })
        return df

class SlidingRadar(Radar):
    def __init__(self, radar_id: str, pri_start: float, pri_end: float, pulses_per_slide: int, freq_mean: float, **kwargs):
        super().__init__(radar_id, freq_mean, **kwargs)
        self.pri_start = pri_start
        self.pri_end = pri_end
        self.pulses_per_slide = pulses_per_slide

    def generate_pdws(self, num_pulses: int, start_time: float = 0.0, toa_noise_std: float = 0.0, freq_noise_std: float = 0.0) -> pd.DataFrame:
        slide_pattern = np.linspace(self.pri_start, self.pri_end, self.pulses_per_slide)
        cycles = np.tile(slide_pattern, int(np.ceil(num_pulses / self.pulses_per_slide)))
        pris = cycles[:num_pulses]
        
        toas = start_time + np.cumsum(pris) - pris[0]
        
        if toa_noise_std > 0:
            toas += np.random.normal(0, toa_noise_std, num_pulses)
            pris = np.append([pris[0]], np.diff(toas))
            
        freqs = self._generate_frequencies(num_pulses, freq_noise_std)
        
        df = pd.DataFrame({
            "Radar_ID": self.radar_id,
            "TOA": toas,
            "PRI": pris,
            "Frequency": freqs
        })
        return df

