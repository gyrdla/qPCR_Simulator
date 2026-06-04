# analysis/ct_calculator.py
import numpy as np
import warnings
from typing import Dict, List
from scipy.signal import savgol_filter
from analysis.curve_quality import adaptive_baseline_correction, calculate_curve_metrics

# Numpy runtime uyarılarını (divide, invalid value) geçici olarak bastır
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

def calculate_ct(signal: List[float], method: str = 'hybrid') -> Dict:
    raw = np.array(signal, dtype=float)
    n = len(raw)
    if n < 20:
        return {'ct': float('nan'), 'confidence': 0.0, 'r2_fit': 0.0, 'curve_quality': {}}

    # 1. Adaptif Baseline Düzeltmesi
    corrected = adaptive_baseline_correction(raw)
    
    # Threshold stabilitesi için baseline ofsetini geri ekle
    baseline_mean = np.mean(raw[:15])
    corrected += baseline_mean

    # 2. Threshold Yöntemi
    bl_mean = np.mean(corrected[:15])
    bl_sd = np.std(corrected[:15])
    threshold = bl_mean + 10 * bl_sd
    above_thresh = np.where(corrected > threshold)[0]
    ct_thresh = float(above_thresh[0]) + 0.5 if len(above_thresh) > 0 else 40.0

    # 3. 2nd Türev Maks (Cy0 Yaklaşımı)
    if n >= 5:
        smoothed = savgol_filter(corrected, window_length=5, polyorder=2)
        d2 = np.gradient(np.gradient(smoothed))
        cy0_idx = np.argmax(d2)
        ct_cy0 = float(cy0_idx) + 0.5
    else:
        ct_cy0 = ct_thresh

    # 4. Hibrit Seçim
    if method == 'hybrid':
        if abs(ct_thresh - ct_cy0) < 2.0:
            ct_val = (ct_thresh + ct_cy0) / 2.0
            confidence = 0.95
        else:
            ct_val = ct_thresh
            confidence = 0.75
    else:
        ct_val = ct_thresh if method == 'threshold' else ct_cy0
        confidence = 0.85

    # 5. R² Fit (Log-lineer faz)
    p70 = np.percentile(corrected, 70)
    mask_exp = (corrected > threshold) & (corrected < p70)
    
    r2 = 0.0
    if np.sum(mask_exp) >= 3:
        # Baseline'i çıkararak saf büyüme fazının log-lineerliğini fit et
        y_vals = corrected[mask_exp] - bl_mean
        y = np.log10(np.maximum(y_vals, 1e-6)) # Negatif log uyarısını önle
        x = np.arange(n)[mask_exp]
        try:
            p = np.polyfit(x, y, 1)
            y_fit = np.polyval(p, x)
            ss_res = np.sum((y - y_fit)**2)
            ss_tot = np.sum((y - np.mean(y))**2)
            r2 = float(1 - ss_res/ss_tot) if ss_tot > 1e-6 else 0.99
        except (ValueError, np.linalg.LinAlgError):
            r2 = 0.0 # DLASCLS hatası olursa 0 döndür

    # 6. Eğri Kalite Metrikleri
    curve_quality = calculate_curve_metrics(corrected)

    return {
        'ct': float(np.clip(ct_val, 0, n)),
        'confidence': confidence,
        'r2_fit': round(r2, 4),
        'curve_quality': curve_quality,
        'baseline_corrected': True
    }