import numpy as np
import pandas as pd
from typing import List, Optional

class Radar:
    def __init__(self, radar_id: str, freq_mean: float, freq_mode: str = "constant", freq_hopping_values: Optional[List[float]] = None,
                 poi: float = 1.0, multipath_prob: float = 0.0, multipath_delay_mean: float = 1.0, multipath_delay_std: float = 0.2,
                 pw_mean: float = 1.0, amp_mean: float = -50.0, aoa_mean: float = 90.0,
                 scan_period: float = 0.0, aoa_drift_rate: float = 0.0, stretch_pw_on_multipath: bool = False):
        """
        Base Radar Class.
        :param pw_mean: Pulse width in microseconds.
        :param amp_mean: Amplitude in dBm.
        :param aoa_mean: Angle of arrival in degrees (0 to 360).
        :param scan_period: Time in microseconds for a full 360-degree antenna rotation (0 for static/non-scanning).
        :param aoa_drift_rate: Rate of change of AOA in degrees per second (simulating platform movement).
        :param stretch_pw_on_multipath: If True, echoes merge into the main pulse, stretching its PW.
        """
        self.radar_id = radar_id
        self.freq_mean = freq_mean
        self.freq_mode = freq_mode
        self.freq_hopping_values = freq_hopping_values if freq_hopping_values else [freq_mean]
        self.poi = poi
        self.multipath_prob = multipath_prob
        self.multipath_delay_mean = multipath_delay_mean
        self.multipath_delay_std = multipath_delay_std
        self.stretch_pw_on_multipath = stretch_pw_on_multipath
        
        self.pw_mean = pw_mean
        self.amp_mean = amp_mean
        self.aoa_mean = aoa_mean
        self.scan_period = scan_period
        self.scan_phase = np.random.uniform(0, 360.0) if scan_period > 0 else 0.0
        self.aoa_drift_rate = aoa_drift_rate

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

    def generate_pdws(self, duration: float, start_time: float = 0.0, 
                      toa_noise_std: float = 0.0, freq_noise_std: float = 0.0,
                      pw_noise_std: float = 0.1, amp_noise_std: float = 2.0, aoa_noise_std: float = 1.0) -> pd.DataFrame:
        raise NotImplementedError("This method should be overridden by subclasses")

    def _finalize_df(self, toas: np.ndarray, pris: np.ndarray, duration: float, start_time: float, 
                     toa_noise_std: float, freq_noise_std: float,
                     pw_noise_std: float, amp_noise_std: float, aoa_noise_std: float) -> pd.DataFrame:
        
        # 1. Filter by duration
        valid_idx = toas <= (start_time + duration)
        toas = toas[valid_idx]
        pris = pris[valid_idx]
        num_pulses = len(toas)
        
        # 2. Generate frequencies BEFORE POI drop, so the internal hopper state advances correctly!
        freqs = self._generate_frequencies(num_pulses, freq_noise_std)
        
        # 3. Apply Emitter-Level POI (Missing Pulses)
        if self.poi < 1.0:
            intercepted = np.random.rand(num_pulses) < self.poi
            toas = toas[intercepted]
            pris = pris[intercepted]
            freqs = freqs[intercepted]
            num_pulses = len(toas)

        if toa_noise_std > 0 and num_pulses > 0:
            toas += np.random.normal(0, toa_noise_std, num_pulses)
            
        # Generate Secondary Parameters
        pws = np.random.normal(self.pw_mean, pw_noise_std, num_pulses)
        pws = np.maximum(0.01, pws) # Ensure PW is positive
        
        # Baseline Amplitude and AOA
        amps = np.full(num_pulses, self.amp_mean)
        aoas = np.full(num_pulses, self.aoa_mean)
        
        # Apply Antenna Scan Pattern for Amplitude Modulations (Sinc^2 shape)
        if self.scan_period > 0 and num_pulses > 0:
            # Calculate angle relative to receiver, adding the random starting phase
            theta = (((toas % self.scan_period) / self.scan_period) * 360.0 + self.scan_phase) % 360.0
            theta[theta > 180] -= 360.0
            
            beam_width = 5.0 # Degrees to first null
            x = theta / beam_width
            # np.sinc(x) is sin(pi*x)/(pi*x)
            sinc_val = np.sinc(x)
            gain = 20.0 * np.log10(np.abs(sinc_val) + 1e-5) # 20*log10(sinc) = 10*log10(sinc^2)
            gain = np.maximum(gain, -40.0) # Floor at -40 dB
            amps += gain
            
        # Apply Kinematic AOA Drift
        if self.aoa_drift_rate != 0 and num_pulses > 0:
            # aoa_drift_rate is in degrees per second, TOA is in microseconds
            aoas += self.aoa_drift_rate * (toas / 1_000_000.0)
            
        # Add measurement noise
        amps += np.random.normal(0, amp_noise_std, num_pulses)
        aoas = (aoas + np.random.normal(0, aoa_noise_std, num_pulses)) % 360.0
        
        df = pd.DataFrame({
            "Radar_ID": self.radar_id,
            "TOA": toas,
            "PRI": pris,
            "Frequency": freqs,
            "PW": pws,
            "Amplitude": amps,
            "AOA": aoas
        })
        
        # Apply Emitter-Level Multipath Echoes
        if self.multipath_prob > 0 and num_pulses > 0:
            echo_mask = np.random.rand(num_pulses) < self.multipath_prob
            num_echoes = np.sum(echo_mask)
            if num_echoes > 0:
                delays = np.random.normal(self.multipath_delay_mean, self.multipath_delay_std, num_echoes)
                delays = np.abs(delays)
                
                if self.stretch_pw_on_multipath:
                    # Echo merges with main pulse, stretching its Pulse Width
                    # Using loc to safely modify the DataFrame
                    df.loc[echo_mask, 'PW'] += delays
                else:
                    # Create separate delayed echo pulses
                    echo_toas = toas[echo_mask] + delays
                    echo_freqs = freqs[echo_mask] + np.random.normal(0, freq_noise_std, num_echoes)
                    
                    # Echoes: Same PW, lower Amplitude, random AOA
                    echo_pws = pws[echo_mask] + np.random.normal(0, 0.05, num_echoes) # Slight distortion in PW
                    echo_amps = amps[echo_mask] - np.random.uniform(5.0, 15.0, num_echoes) # 5 to 15 dB lower
                    echo_aoas = np.random.uniform(0.0, 360.0, num_echoes) # Completely random AOA
                    
                    echo_df = pd.DataFrame({
                        "Radar_ID": self.radar_id + "_ECHO", 
                        "TOA": echo_toas,
                        "PRI": 0.0, 
                        "Frequency": echo_freqs,
                        "PW": echo_pws,
                        "Amplitude": echo_amps,
                        "AOA": echo_aoas
                    })
                    df = pd.concat([df, echo_df], ignore_index=True)
                
        df = df.sort_values("TOA").reset_index(drop=True)
        return df


class StableRadar(Radar):
    def __init__(self, radar_id: str, pri: float, freq_mean: float, **kwargs):
        super().__init__(radar_id, freq_mean, **kwargs)
        self.pri = pri

    def generate_pdws(self, duration: float, start_time: float = 0.0, 
                      toa_noise_std: float = 0.0, freq_noise_std: float = 0.0,
                      pw_noise_std: float = 0.1, amp_noise_std: float = 2.0, aoa_noise_std: float = 1.0) -> pd.DataFrame:
        num_pulses_est = int(np.ceil(duration / self.pri)) + 2
        pris = np.full(num_pulses_est, self.pri)
        toas = start_time + np.cumsum(pris) - self.pri
        return self._finalize_df(toas, pris, duration, start_time, toa_noise_std, freq_noise_std, pw_noise_std, amp_noise_std, aoa_noise_std)


class JitterRadar(Radar):
    def __init__(self, radar_id: str, pri_mean: float, pri_jitter_std: float, freq_mean: float, **kwargs):
        super().__init__(radar_id, freq_mean, **kwargs)
        self.pri_mean = pri_mean
        self.pri_jitter_std = pri_jitter_std

    def generate_pdws(self, duration: float, start_time: float = 0.0, 
                      toa_noise_std: float = 0.0, freq_noise_std: float = 0.0,
                      pw_noise_std: float = 0.1, amp_noise_std: float = 2.0, aoa_noise_std: float = 1.0) -> pd.DataFrame:
        num_pulses_est = int(np.ceil(duration / max(1.0, (self.pri_mean - self.pri_jitter_std*3)))) + 5
        pris = np.random.normal(self.pri_mean, self.pri_jitter_std, num_pulses_est)
        pris = np.maximum(pris, 1.0) # Prevent negative PRIs
        toas = start_time + np.cumsum(pris) - pris[0]
        return self._finalize_df(toas, pris, duration, start_time, toa_noise_std, freq_noise_std, pw_noise_std, amp_noise_std, aoa_noise_std)


class StaggerRadar(Radar):
    def __init__(self, radar_id: str, stagger_pris: List[float], freq_mean: float, **kwargs):
        super().__init__(radar_id, freq_mean, **kwargs)
        self.stagger_pris = stagger_pris

    def generate_pdws(self, duration: float, start_time: float = 0.0, 
                      toa_noise_std: float = 0.0, freq_noise_std: float = 0.0,
                      pw_noise_std: float = 0.1, amp_noise_std: float = 2.0, aoa_noise_std: float = 1.0) -> pd.DataFrame:
        avg_pri = np.mean(self.stagger_pris)
        num_pulses_est = int(np.ceil(duration / avg_pri)) + len(self.stagger_pris)
        cycles = np.tile(self.stagger_pris, int(np.ceil(num_pulses_est / len(self.stagger_pris))))
        pris = cycles[:num_pulses_est]
        toas = start_time + np.cumsum(pris) - pris[0]
        return self._finalize_df(toas, pris, duration, start_time, toa_noise_std, freq_noise_std, pw_noise_std, amp_noise_std, aoa_noise_std)


class DwellAndSwitchRadar(Radar):
    def __init__(self, radar_id: str, dwell_pris: List[float], pulses_per_dwell: int, freq_mean: float, **kwargs):
        super().__init__(radar_id, freq_mean, **kwargs)
        self.dwell_pris = dwell_pris
        self.pulses_per_dwell = pulses_per_dwell

    def generate_pdws(self, duration: float, start_time: float = 0.0, 
                      toa_noise_std: float = 0.0, freq_noise_std: float = 0.0,
                      pw_noise_std: float = 0.1, amp_noise_std: float = 2.0, aoa_noise_std: float = 1.0) -> pd.DataFrame:
        avg_pri = np.mean(self.dwell_pris)
        num_pulses_est = int(np.ceil(duration / avg_pri)) + self.pulses_per_dwell * len(self.dwell_pris)
        
        # Create dwell pattern
        pattern = []
        for pri in self.dwell_pris:
            pattern.extend([pri] * self.pulses_per_dwell)
            
        cycles = np.tile(pattern, int(np.ceil(num_pulses_est / len(pattern))))
        pris = cycles[:num_pulses_est]
        toas = start_time + np.cumsum(pris) - pris[0]
        return self._finalize_df(toas, pris, duration, start_time, toa_noise_std, freq_noise_std, pw_noise_std, amp_noise_std, aoa_noise_std)


class SlidingRadar(Radar):
    def __init__(self, radar_id: str, pri_start: float, pri_end: float, pulses_per_slide: int, freq_mean: float, **kwargs):
        super().__init__(radar_id, freq_mean, **kwargs)
        self.pri_start = pri_start
        self.pri_end = pri_end
        self.pulses_per_slide = pulses_per_slide

    def generate_pdws(self, duration: float, start_time: float = 0.0, 
                      toa_noise_std: float = 0.0, freq_noise_std: float = 0.0,
                      pw_noise_std: float = 0.1, amp_noise_std: float = 2.0, aoa_noise_std: float = 1.0) -> pd.DataFrame:
        avg_pri = min(self.pri_start, self.pri_end)
        num_pulses_est = int(np.ceil(duration / avg_pri)) + self.pulses_per_slide
        slide_pattern = np.linspace(self.pri_start, self.pri_end, self.pulses_per_slide)
        cycles = np.tile(slide_pattern, int(np.ceil(num_pulses_est / self.pulses_per_slide)))
        pris = cycles[:num_pulses_est]
        toas = start_time + np.cumsum(pris) - pris[0]
        return self._finalize_df(toas, pris, duration, start_time, toa_noise_std, freq_noise_std, pw_noise_std, amp_noise_std, aoa_noise_std)


class Environment:
    def __init__(self):
        self.radars = []

    def add_radar(self, radar: Radar):
        self.radars.append(radar)

    def generate(self, duration: float, start_time: float = 0.0, 
                 toa_noise_std: float = 0.0, freq_noise_std: float = 0.0,
                 pw_noise_std: float = 0.1, amp_noise_std: float = 2.0, aoa_noise_std: float = 1.0,
                 global_drop_rate: float = 0.0, noise_rate: float = 0.0,
                 quantize: bool = False, toa_res: float = 0.01, freq_res: float = 1.0,
                 pw_res: float = 0.05, amp_res: float = 0.5, aoa_res: float = 0.1) -> pd.DataFrame:
        dfs = []
        for radar in self.radars:
            offset = np.random.uniform(0, 2000)
            df = radar.generate_pdws(
                duration=duration, 
                start_time=start_time + offset, 
                toa_noise_std=toa_noise_std, 
                freq_noise_std=freq_noise_std,
                pw_noise_std=pw_noise_std,
                amp_noise_std=amp_noise_std,
                aoa_noise_std=aoa_noise_std
            )
            dfs.append(df)
            
        if not dfs:
            interleaved_df = pd.DataFrame(columns=["Radar_ID", "TOA", "PRI", "Frequency", "PW", "Amplitude", "AOA"])
        else:
            interleaved_df = pd.concat(dfs, ignore_index=True)
            
        # Add Global Random Noise Pulses
        duration_seconds = duration / 1_000_000.0
        num_noise_pulses = int(np.random.poisson(noise_rate * duration_seconds))
        if num_noise_pulses > 0:
            noise_toas = np.random.uniform(start_time, start_time + duration, num_noise_pulses)
            noise_freqs = np.random.uniform(2000.0, 18000.0, num_noise_pulses)
            noise_pws = np.random.uniform(0.1, 10.0, num_noise_pulses)
            noise_amps = np.random.uniform(-90.0, -50.0, num_noise_pulses)
            noise_aoas = np.random.uniform(0.0, 360.0, num_noise_pulses)
            
            noise_df = pd.DataFrame({
                "Radar_ID": "NOISE",
                "TOA": noise_toas,
                "PRI": 0.0,
                "Frequency": noise_freqs,
                "PW": noise_pws,
                "Amplitude": noise_amps,
                "AOA": noise_aoas
            })
            interleaved_df = pd.concat([interleaved_df, noise_df], ignore_index=True)

        interleaved_df = interleaved_df.sort_values(by="TOA").reset_index(drop=True)
        
        # Pulse-on-Pulse Collision (Receiver Dead Time)
        filtered_indices = []
        if len(interleaved_df) > 0:
            current_end_time = -1
            current_max_amp = -np.inf
            current_idx = -1
            
            for i in range(len(interleaved_df)):
                toa = interleaved_df.at[i, "TOA"]
                pw = interleaved_df.at[i, "PW"]
                amp = interleaved_df.at[i, "Amplitude"]
                
                if toa >= current_end_time:
                    # No overlap with previous processed group
                    if current_idx != -1:
                        filtered_indices.append(current_idx)
                    current_idx = i
                    current_end_time = toa + pw
                    current_max_amp = amp
                else:
                    # Overlap! Pulse collision detected.
                    # Keep the one with the higher amplitude.
                    if amp > current_max_amp:
                        current_idx = i
                        current_end_time = max(current_end_time, toa + pw)
                        current_max_amp = amp
                        
            if current_idx != -1:
                filtered_indices.append(current_idx)
                
            interleaved_df = interleaved_df.iloc[filtered_indices].reset_index(drop=True)

        # Apply Global Drop Rate
        if global_drop_rate > 0 and len(interleaved_df) > 0:
            keep_mask = np.random.rand(len(interleaved_df)) >= global_drop_rate
            interleaved_df = interleaved_df[keep_mask].reset_index(drop=True)
            
        # Apply Digital Quantization (Optional)
        if quantize and len(interleaved_df) > 0:
            interleaved_df["TOA"] = np.round(interleaved_df["TOA"] / toa_res) * toa_res
            interleaved_df["Frequency"] = np.round(interleaved_df["Frequency"] / freq_res) * freq_res
            interleaved_df["PW"] = np.round(interleaved_df["PW"] / pw_res) * pw_res
            interleaved_df["Amplitude"] = np.round(interleaved_df["Amplitude"] / amp_res) * amp_res
            interleaved_df["AOA"] = np.round(interleaved_df["AOA"] / aoa_res) * aoa_res
        
        interleaved_df["Measured_Delta_TOA"] = interleaved_df["TOA"].diff().fillna(0)
        
        return interleaved_df
