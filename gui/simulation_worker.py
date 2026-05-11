# gui/simulation_worker.py
from PyQt6.QtCore import QThread, pyqtSignal
from typing import Dict, Any
from core.simulation import run_qpcr_cycles
from core.reagents import ReactionMix
from core.thermodynamics import calculate_tm
from core.master_mix import get_preset, apply_preset_to_mix
from core.thermal_profile import LC480_STANDARD, QUANTSTUDIO_FAST
from analysis.signal import generate_signal
from analysis.ct_calculator import calculate_ct
from analysis.replicates import ReplicateSimulator
import numpy as np

class SimulationWorker(QThread):
    progress = pyqtSignal(int, float)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, params: Dict[str, Any]):
        super().__init__()
        self.params = params

    def run(self):
        try:
            fwd = self.params.get('fwd_primer', '').strip()
            rev = self.params.get('rev_primer', '').strip()
            if not fwd or not rev:
                raise ValueError("Forward ve Reverse primer sekansları boş bırakılamaz.")

            cycles = int(self.params.get('cycles', 40))
            ta = float(self.params.get('ta_temp', 60.0))
            try:
                template_copies = float(self.params.get('template_copies', '1000'))
            except (ValueError, TypeError):
                template_copies = 1000.0
            primer_conc = float(self.params.get('primer_conc', 250e-9))

            preset_name = self.params.get('master_mix_preset', 'Manual')
            if preset_name != 'Manual':
                preset = get_preset(preset_name)
                mix_cfg = apply_preset_to_mix(preset)
                mg, dntp = mix_cfg['mg_total_mM'], mix_cfg['dntp_total_mM']
                primer_uM, poly_U = mix_cfg['primer_uM'], mix_cfg['polymerase_U']
                dye = mix_cfg['dye_type']
            else:
                mg = float(self.params.get('mg_conc', 3.0))
                dntp = float(self.params.get('dntp_conc', 0.2))
                primer_uM = primer_conc * 1e6
                poly_U = 1.0
                dye = self.params.get('dye_type', 'SYBR')

            tm_fwd = calculate_tm(fwd, primer_conc=primer_conc, mg_mM=mg, dntp_mM=dntp)
            tm_rev = calculate_tm(rev, primer_conc=primer_conc, mg_mM=mg, dntp_mM=dntp)
            tm_avg = (tm_fwd + tm_rev) / 2

            thermal_name = self.params.get('thermal_profile', 'LC480 Standard')
            profile = LC480_STANDARD if 'LC480' in thermal_name else QUANTSTUDIO_FAST
            time_factor = profile.get_efficiency_time_factor(ta)

            n_tech = int(self.params.get('tech_rep', 1))
            n_bio = int(self.params.get('bio_rep', 1))
            pip_cv = float(self.params.get('pipette_cv', 0.02))
            th_sd = float(self.params.get('thermal_sd', 0.3))

            if n_tech * n_bio > 1:
                base_params = {
                    'copies': template_copies, 'mg': mg, 'dntp': dntp,
                    'primer_uM': primer_uM, 'polymerase_U': poly_U,
                    'ta': ta, 'tm': tm_avg, 'cycles': cycles, 'dye': dye
                }
                sim = ReplicateSimulator(base_params, n_tech, n_bio, pip_cv, th_sd, time_factor)
                rep_res = sim.run()
                
                mix = ReactionMix(mg, dntp, primer_uM, poly_U)
                amp_curve = run_qpcr_cycles(template_copies, cycles, mix, tm_avg, ta, time_factor)
                raw_signal = generate_signal(amp_curve, dye=dye)
                ct_val = calculate_ct(raw_signal, method='hybrid')['ct']
                eff = self._estimate_efficiency(amp_curve)

                self.finished.emit({
                    'cycles': list(range(cycles)), 'signal': raw_signal,
                    'ct': ct_val, 'tm_fwd': tm_fwd, 'tm_rev': tm_rev,
                    'efficiency': eff, 'dye': dye,
                    'replicates': rep_res, 'is_replicate': True
                })
            else:
                mix = ReactionMix(mg, dntp, primer_uM, poly_U)
                amp_curve = run_qpcr_cycles(template_copies, cycles, mix, tm_avg, ta, time_factor)
                
                for i, val in enumerate(amp_curve):
                    self.progress.emit(i + 1, val)
                    
                raw_signal = generate_signal(amp_curve, dye=dye)
                ct_val = calculate_ct(raw_signal, method='hybrid')['ct']
                eff = self._estimate_efficiency(amp_curve)

                self.finished.emit({
                    'cycles': list(range(cycles)), 'signal': raw_signal,
                    'ct': ct_val, 'tm_fwd': tm_fwd, 'tm_rev': tm_rev,
                    'efficiency': eff, 'dye': dye, 'is_replicate': False
                })
        except Exception as e:
            self.error.emit(str(e))

    def _estimate_efficiency(self, amp_curve: list) -> float:
        """Adaptif verimlilik: dinamik aralığa göre log-lineer fazı otomatik izole eder"""
        y = np.array(amp_curve, dtype=float)
        if len(y) < 10 or np.max(y) <= np.min(y):
            return 0.90
            
        y_min, y_max = np.min(y), np.max(y)
        dyn = y_max - y_min
        if dyn < 1e-6:
            return 0.90
            
        mask = (y > y_min + 0.03 * dyn) & (y < y_min + 0.40 * dyn)
        if np.sum(mask) < 4:
            mask = (y > y_min + 0.05 * dyn) & (y < y_min + 0.25 * dyn)
            if np.sum(mask) < 4:
                return 0.90
                
        slope, _ = np.polyfit(np.arange(len(y))[mask], np.log10(y[mask]), 1)
        eff = 10**(-1 / slope) - 1 if slope != 0 else 0.90
        return max(0.75, min(eff, 1.08))