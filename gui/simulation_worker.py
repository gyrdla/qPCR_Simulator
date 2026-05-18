# gui/simulation_worker.py
from PyQt6.QtCore import QThread, pyqtSignal
from typing import Dict, Any, List
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
            try: template_copies = float(self.params.get('template_copies', '1000'))
            except (ValueError, TypeError): template_copies = 1000.0
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

            plate_wells = self.params.get('plate_wells', None)
            if plate_wells and isinstance(plate_wells, list) and len(plate_wells) > 1:
                self._run_plate_mode(plate_wells, cycles, ta, tm_avg, tm_fwd, tm_rev, mg, dntp, primer_uM, poly_U, dye, time_factor)
            else:
                self._run_single_mode(template_copies, cycles, ta, tm_avg, tm_fwd, tm_rev, mg, dntp, primer_uM, poly_U, dye, time_factor)
        except Exception as e:
            self.error.emit(str(e))

    def _run_single_mode(self, copies, cycles, ta, tm_avg, tm_fwd, tm_rev, mg, dntp, primer_uM, poly_U, dye, time_factor):
        mix = ReactionMix(mg, dntp, primer_uM, poly_U)
        amp_curve = run_qpcr_cycles(copies, cycles, mix, tm_avg, ta, time_factor)
        for i, val in enumerate(amp_curve):
            self.progress.emit(i + 1, val)
        opt_cfg = self.params.get('optics', {})
        raw_signal = generate_signal(amp_curve, dye=dye, 
                                     calibration_offset=opt_cfg.get('calibration_offset', 0.0),
                                     calibration_drift=opt_cfg.get('calibration_drift', 0.0))
        ct_val = calculate_ct(raw_signal, method='hybrid')['ct']
        eff = self._estimate_efficiency(amp_curve)
        self.finished.emit({
            'cycles': list(range(cycles)), 'signal': raw_signal,
            'ct': ct_val, 'tm_fwd': tm_fwd, 'tm_rev': tm_rev,
            'efficiency': eff, 'dye': dye, 'is_replicate': False
        })

    def _run_plate_mode(self, wells: List[Dict], cycles, ta, tm_avg, tm_fwd, tm_rev, mg, dntp, primer_uM, poly_U, dye, time_factor):
        from core.housekeeping import calculate_ddct_and_fc, calculate_genorm_m
        
        all_cts, all_effs, all_signals = [], [], []
        target_cts, ref_cts = [], []
        ref_by_name = {}
        
        for idx, w in enumerate(wells):
            w_copies = w.get('copies', 1000)
            w_type = w.get('type', 'TARGET')
            w_thermal = w.get('thermal_well_factor', 1.0)
            w_optical = w.get('optical_well_factor', 1.0)
            
            if w_type == "NTC" or w_copies <= 0:
                base_sig = [250.0 + np.random.normal(0, 2.5) for _ in range(cycles)]
                all_cts.append(40.0)
                all_effs.append(0.0)
                all_signals.append(base_sig)
                self.progress.emit(idx + 1, 40.0)
                continue
                
            w_ta = ta + np.random.normal(0.0, 0.25 * w_thermal)
            mix = ReactionMix(mg, dntp, primer_uM, poly_U)
            amp = run_qpcr_cycles(w_copies, cycles, mix, tm_avg, w_ta, time_factor)
            opt_cfg = self.params.get('optics', {})
            sig = generate_signal(amp, dye=dye,
            calibration_offset=opt_cfg.get('calibration_offset', 0.0),
            calibration_drift=opt_cfg.get('calibration_drift', 0.0))
            sig = [s * w_optical for s in sig]
            
            ct = calculate_ct(sig, method='hybrid')['ct']
            eff = self._estimate_efficiency(amp)
            all_cts.append(ct)
            all_effs.append(eff)
            all_signals.append(sig)
            self.progress.emit(idx + 1, ct)
            
            if w_type == "TARGET":
                target_cts.append(ct)
            elif w_type == "REFERENCE":
                ref_cts.append(ct)
                rname = w.get('name', 'REF')
                ref_by_name.setdefault(rname, []).append(ct)

        # Normalizasyon
        norm_res = None
        if ref_cts and target_cts:
            cal_target = target_cts[:1]
            cal_ref = ref_cts[:len(ref_cts)]
            norm_res = calculate_ddct_and_fc(target_cts, ref_cts, cal_target, cal_ref)
            ref_lists = list(ref_by_name.values())
            m_val = calculate_genorm_m(ref_lists) if len(ref_lists) >= 2 else 0.0
            norm_res['genorm_m'] = m_val
            norm_res['ref_stable'] = m_val < 0.5 if m_val > 0 else True

        # Diagnostik Analiz (Plate modunda, emit öncesi)
        diag_cfg = self.params.get('diagnostics', {})
        diag_res = self._analyze_diagnostics(wells, all_cts, diag_cfg)

        avg_signal = np.mean(all_signals, axis=0).tolist()
        self.finished.emit({
            'cycles': list(range(cycles)), 'signal': avg_signal,
            'plate_signals': all_signals, 'plate_wells': wells,
            'ct': float(np.mean([c for c in all_cts if c < 40.0])) if any(c<40 for c in all_cts) else 40.0,
            'tm_fwd': tm_fwd, 'tm_rev': tm_rev,
            'efficiency': float(np.mean([e for e in all_effs if e > 0])),
            'dye': dye, 'is_replicate': False,
            'plate_cts': all_cts, 'plate_effs': all_effs,
            'normalization': norm_res,
            'diagnostics': diag_res
        })

    def _estimate_efficiency(self, amp_curve: list) -> float:
        y = np.array(amp_curve, dtype=float)
        if len(y) < 10 or np.max(y) <= np.min(y): return 0.90
        y_min, y_max = np.min(y), np.max(y)
        dyn = y_max - y_min
        if dyn < 1e-6: return 0.90
        mask = (y > y_min + 0.03 * dyn) & (y < y_min + 0.40 * dyn)
        if np.sum(mask) < 4:
            mask = (y > y_min + 0.05 * dyn) & (y < y_min + 0.25 * dyn)
            if np.sum(mask) < 4: return 0.90
        slope, _ = np.polyfit(np.arange(len(y))[mask], np.log10(y[mask]), 1)
        eff = 10**(-1 / slope) - 1 if slope != 0 else 0.90
        return max(0.75, min(eff, 1.08))

    def _analyze_diagnostics(self, wells, cts, diag_cfg):
        from core.diagnostics import call_ct, calculate_diagnostic_metrics, estimate_lod
        if not diag_cfg or not diag_cfg.get('enabled'):
            return None

        pos_cut = diag_cfg.get('pos_cutoff', 35.0)
        indet_cut = diag_cfg.get('indet_cutoff', 38.0)
        ntc_contam = diag_cfg.get('ntc_contam_rate', 0.02)

        calls, true_statuses = [], []
        for w, ct in zip(wells, cts):
            w_type = w.get('type', 'TARGET')
            ct_sim = ct
            if w_type == 'NTC' and np.random.random() < ntc_contam:
                ct_sim = np.random.uniform(32.0, 36.0)

            calls.append(call_ct(ct_sim, pos_cut, indet_cut))
            true_statuses.append('NEGATIF' if w_type == 'NTC' or w.get('copies', 0) == 0 else 'POZITIF')

        metrics = calculate_diagnostic_metrics(calls, true_statuses)
        lod_res = estimate_lod([1, 2, 5, 10, 20, 50], n_rep=12)

        return {
            'calls': calls, 'true_statuses': true_statuses,
            'metrics': metrics, 'lod': lod_res,
            'pos_cutoff': pos_cut, 'indet_cutoff': indet_cut,
            'ivd_ready': metrics['sensitivity'] >= 0.95 and metrics['specificity'] >= 0.98
        }