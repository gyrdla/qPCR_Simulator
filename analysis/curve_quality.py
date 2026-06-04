# analysis/curve_quality.py
import numpy as np
from typing import Dict

def adaptive_baseline_correction(signal: np.ndarray, baseline_start: int = 3, baseline_end: int = 15) -> np.ndarray:
    """
    MIQE uyumlu adaptif baseline düzeltmesi.
    Fotobleaching, termal drift veya reaktif heterojenliğini 2. derece polinom ile çıkarır.
    """
    cycles = np.arange(len(signal))
    mask = (cycles >= baseline_start) & (cycles <= baseline_end)
    if np.sum(mask) < 3:
        return signal - np.mean(signal[:baseline_end])
    coeffs = np.polyfit(cycles[mask], signal[mask], deg=2)
    baseline_fit = np.polyval(coeffs, cycles)
    corrected = signal - baseline_fit
    return np.maximum(corrected, 0.0)  # Fiziksel olarak negatif florasan olamaz

def calculate_curve_metrics(signal: np.ndarray) -> Dict:
    """
    Amplifikasyon eğrisinin MIQE kalite metriklerini hesaplar.
    """
    sig = np.array(signal, dtype=float)
    n = len(sig)

    # 1. Baseline Stability (Cycles 3-15)
    bl_mask = np.arange(3, min(16, n))
    bl_sd = float(np.std(sig[bl_mask]))
    bl_slope = float(np.polyfit(np.arange(len(bl_mask)), sig[bl_mask], 1)[0])

    # 2. Plateau Slope (Cycles 30-40)
    plt_mask = np.arange(min(30, n-1), n)
    plateau_slope = float(np.polyfit(np.arange(len(plt_mask)), sig[plt_mask], 1)[0])

    # 3. Hook Effect Detection (Platodan sonra >%10 düşüş)
    max_idx = np.argmax(sig)
    post_max = sig[max_idx:]
    hook_effect = bool(len(post_max) > 5 and (post_max[0] - post_max[-1]) > (0.10 * sig[max_idx]))

    # 4. Symmetry Index (Yükselme vs Düşüş süresi oranı)
    max_val = sig[max_idx]
    half_max = max_val / 2.0
    indices_above = np.where(sig[:max_idx] >= half_max)[0]
    if len(indices_above) == 0:
        symmetry = 1.0
    else:
        rise_time = max_idx - indices_above[0]
        fall_time = n - max_idx if max_idx < n else 1
        symmetry = float(rise_time / max(fall_time, 1))

    # 5. Composite QC Score (0-100)
    score = 100.0
    if bl_sd > 5.0: score -= 20
    if abs(bl_slope) > 2.0: score -= 15
    if abs(plateau_slope) > 5.0: score -= 15
    if hook_effect: score -= 25
    if symmetry < 0.6 or symmetry > 1.8: score -= 15
    score = max(0.0, min(100.0, score))

    status = "✅ İYİ" if score >= 85 else ("⚠️ ORTA" if score >= 60 else "❌ ZAYIF")

    return {
        'baseline_sd': round(bl_sd, 2),
        'baseline_slope': round(bl_slope, 2),
        'plateau_slope': round(plateau_slope, 2),
        'hook_effect': hook_effect,
        'symmetry_index': round(symmetry, 2),
        'qc_score': round(score, 1),
        'status': status
    }