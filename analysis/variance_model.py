# analysis/variance_model.py
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class VarianceConfig:
    # Intra-run (well-to-well, aynı plakada)
    pipette_cv: float = 0.02          # %2 pipetleme hatası
    thermal_well_sd: float = 0.25     # °C well-to-well termal fark
    optical_noise_cv: float = 0.008   # PMT/optik gürültü CV
    
    # Inter-run (günler arası, lot, kalibrasyon)
    enzyme_lot_cv: float = 0.08       # %8 enzim aktivite lot varyasyonu
    mg_batch_cv: float = 0.05         # %5 Mg²⁺ konsantrasyon batch farkı
    calibration_drift_sd: float = 0.15 # °C günler arası blok kalibrasyon drifti
    ambient_effect_sd: float = 0.10   # °C ambient sıcaklık/nem dolaylı etkisi

class HierarchicalVarianceSimulator:
    """
    Intra/Inter-run varyasyon modelleyici.
    Nested Monte Carlo: Dış döngü inter-run, iç döngü intra-run.
    """
    def __init__(self, config: VarianceConfig = VarianceConfig()):
        self.cfg = config

    def apply_inter_run_shift(self, base_params: Dict) -> Dict:
        """Günler arası / lot bazlı sistemik kayma"""
        shifted = base_params.copy()
        shifted['polymerase_U'] *= np.random.normal(1.0, self.cfg.enzyme_lot_cv)
        shifted['mg_total_mM'] *= np.random.normal(1.0, self.cfg.mg_batch_cv)
        shifted['ta_temp'] += np.random.normal(0.0, self.cfg.calibration_drift_sd + self.cfg.ambient_effect_sd)
        return shifted

    def apply_intra_run_noise(self, well_params: Dict, well_id: int, total_wells: int) -> Dict:
        """Well-to-well pipet, termal gradient, optik noise"""
        noisy = well_params.copy()
        noisy['primer_uM'] *= np.random.normal(1.0, self.cfg.pipette_cv)
        noisy['template_copies'] = max(1, np.random.poisson(noisy['template_copies']))
        
        # Edge effect: plaka kenarları daha fazla termal varyasyon görür
        edge_factor = 1.5 if well_id % 12 in (0, 11) or well_id // 12 in (0, 7) else 1.0
        noisy['ta_temp'] += np.random.normal(0.0, self.cfg.thermal_well_sd * edge_factor)
        noisy['optical_noise_cv'] = self.cfg.optical_noise_cv * np.random.uniform(0.8, 1.2)
        return noisy

    def run_nested(self, base_params: Dict, simulator_func: callable, n_runs: int = 3, wells_per_run: int = 8) -> Dict:
        """
        Inter-run (n_runs) × Intra-run (wells_per_run) nested simülasyon.
        simulator_func: (params) -> {'ct': float, 'efficiency': float, 'signal': list}
        """
        all_results = []
        for run in range(n_runs):
            run_params = self.apply_inter_run_shift(base_params)
            run_cts, run_effs = [], []
            for w in range(wells_per_run):
                well_params = self.apply_intra_run_noise(run_params, w, wells_per_run)
                res = simulator_func(well_params)
                run_cts.append(res['ct'])
                run_effs.append(res['efficiency'])
                all_results.append({'run': run+1, 'well': w+1, **res})
                
        cts = np.array([r['ct'] for r in all_results])
        effs = np.array([r['efficiency'] for r in all_results])
        
        # Varyasyon dekompozisyonu (ANOVA benzeri)
        intra_var = np.mean([np.var(cts[i*wells_per_run:(i+1)*wells_per_run]) for i in range(n_runs)])
        inter_var = np.var([np.mean(cts[i*wells_per_run:(i+1)*wells_per_run]) for i in range(n_runs)])
        total_var = intra_var + inter_var
        
        return {
            'mean_ct': float(np.mean(cts)),
            'sd_ct': float(np.std(cts, ddof=1)),
            'cv_pct': float(np.std(cts, ddof=1) / np.mean(cts) * 100) if np.mean(cts) > 0 else 0.0,
            'intra_run_cv': float(np.sqrt(intra_var) / np.mean(cts) * 100) if np.mean(cts) > 0 else 0.0,
            'inter_run_cv': float(np.sqrt(inter_var) / np.mean(cts) * 100) if np.mean(cts) > 0 else 0.0,
            'mean_efficiency': float(np.mean(effs)),
            'n_total': len(all_results),
            'details': all_results
        }