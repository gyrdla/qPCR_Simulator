# analysis/multiplex.py
import numpy as np
from typing import List, Dict
from core.reagents import ReactionMix
from core.simulation import run_qpcr_cycles
from analysis.signal import generate_signal

class MultiplexSimulator:
    """
    Çoklu kanal simülasyonu:
    - Cihaz optik çapraz konuşma matrisi ile unmixing
    - Paylaşılan reaktif havuzu (rekabetçi dNTP/Mg tükenmesi)
    - Kanal bazlı Tm/verimlilik coupling
    """
    def __init__(self, channels: Dict[str, Dict], crosstalk_matrix: np.ndarray = None):
        self.channels = channels
        if crosstalk_matrix is None:
            # FAM / HEX / Cy5 tipik sızıntı matrisi (cihaz kalibrasyonu)
            self.M = np.array([
                [1.00, 0.06, 0.01],
                [0.09, 1.00, 0.04],
                [0.02, 0.07, 1.00]
            ])
        else:
            self.M = crosstalk_matrix
        self.M_inv = np.linalg.inv(self.M)

    def run_coupled(self, cycles: int, mix: ReactionMix, ta_temp: float) -> Dict[str, List[float]]:
        shared_mix = ReactionMix(
            mg_total_mM=mix.mg_total_mM,
            dntp_total_mM=mix.dntp_total_mM,
            primer_uM=mix.primer_uM,
            polymerase_U=mix.polymerase_U
        )

        raw_signals = {}
        for ch, cfg in self.channels.items():
            amp = run_qpcr_cycles(
                initial_copies=cfg.get('copies', 1000),
                cycles=cycles,
                mix=shared_mix,
                tm_primer=cfg.get('tm', 60.0),
                ta_temp=ta_temp
            )
            raw_signals[ch] = generate_signal(amp, dye=cfg.get('dye', 'SYBR'))

        ch_names = list(self.channels.keys())
        obs_matrix = np.array([raw_signals[ch] for ch in ch_names])
        true_matrix = self.M_inv @ obs_matrix

        return {ch: true_matrix[i].tolist() for i, ch in enumerate(ch_names)}