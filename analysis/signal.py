# analysis/signal.py
import numpy as np
from typing import List, Dict, Optional

# Cihaz optik presetleri (ABI/Bio-Rad/Roche fotometri ortalamaları)
OPTICS_PRESETS = {
    'SYBR': {
        'ex_peak': 497.0, 'em_peak': 520.0, 'fwhm_ex': 12.0, 'fwhm_em': 15.0,
        'quantum_yield': 0.78, 'filter_transmission': 0.82, 'pmt_qe': 0.25,
        'pmt_gain': 1.2e6, 'dark_current_rfu': 18.0, 'electronic_noise_rfu': 3.5,
        'shot_noise_factor': 0.045, 'well_pathlength_cm': 0.65, 'meniscus_loss': 0.03
    },
    'TaqMan': {
        'ex_peak': 494.0, 'em_peak': 518.0, 'fwhm_ex': 10.0, 'fwhm_em': 12.0,
        'quantum_yield': 0.85, 'filter_transmission': 0.79, 'pmt_qe': 0.28,
        'pmt_gain': 1.0e6, 'dark_current_rfu': 15.0, 'electronic_noise_rfu': 2.8,
        'shot_noise_factor': 0.038, 'well_pathlength_cm': 0.60, 'meniscus_loss': 0.025
    }
}

def generate_signal(amplicons: List[float], dye: str = 'SYBR', 
                    optics_cfg: Optional[Dict] = None,
                    baseline_rfu: float = 250.0, max_rfu: float = 12000.0,
                    noise_cv: float = 0.008,
                    calibration_offset: float = 0.0, calibration_drift: float = 0.0) -> List[float]:
    """
    First-principles qPCR optik modeli:
    - dsDNA-boyama bağlanma izotermi
    - Beer-Lambert + Quantum Yield + Filtre Transmisyonu + PMT QE
    - Shot noise (Poisson) + Dark current + Elektronik gürültü
    - Well geometrisi, menisküs kaybı, yol uzunluğu
    - Cihaz kalibrasyon offset & drift
    """
    if not amplicons or max(amplicons) == 0:
        return [baseline_rfu] * len(amplicons)
        
    opt = OPTICS_PRESETS.get(dye, OPTICS_PRESETS['SYBR'])
    if optics_cfg:
        opt.update(optics_cfg)
        
    F_max = max(amplicons)
    Kd_norm = 0.02  # SYBR/TaqMan dsDNA bağlanma yarı-doygunluk oranı
    
    amp = np.array(amplicons, dtype=float)
    frac = amp / F_max
    binding = frac / (Kd_norm + frac)
    
    # Fiziksel optik zinciri (RFU ölçeğine normalize)
    optical_eff = (opt['quantum_yield'] * opt['filter_transmission'] * 
                   opt['pmt_qe'] * opt['well_pathlength_cm'] * (1.0 - opt['meniscus_loss']))
    
    # Kalibrasyon: offset + lineer drift (cihaz lot/fotodedektör yaşlanması)
    drift_factor = 1.0 + calibration_drift * np.linspace(0, 1, len(amp))
    rfu_raw = baseline_rfu + binding * (max_rfu - baseline_rfu) * optical_eff * drift_factor + calibration_offset
    
    # Gerçekçi gürültü modeli: Shot (Poisson) + Dark + Elektronik
    shot_std = np.sqrt(np.maximum(rfu_raw, 0) * opt['shot_noise_factor'])
    total_std = np.sqrt(shot_std**2 + opt['dark_current_rfu']**2 + opt['electronic_noise_rfu']**2)
    
    # Heteroscedastic noise (sinyal↑ → gürültü↑, cihaz standardı)
    noisy = rfu_raw + np.random.normal(0, total_std)
    return np.maximum(noisy, 0.0).tolist()