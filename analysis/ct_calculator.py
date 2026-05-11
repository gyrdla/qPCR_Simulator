# analysis/ct_calculator.py
import numpy as np
from typing import List, Dict
from scipy.optimize import curve_fit, OptimizeWarning
from scipy.signal import savgol_filter
import warnings

def sigmoid_4pl(x, a, b, c, d):
    return a / (1 + np.exp(-b * (x - c))) + d

def calculate_ct(fluorescence: List[float], method: str = 'hybrid') -> Dict:
    """
    Hibrit Ct algoritması: Cy0 + 2nd Derivative Max + Threshold fallback
    MIQE uyumlu güvenilirlik skoru (0-1) döner.
    """
    y = np.array(fluorescence, dtype=float)
    x = np.arange(len(y))
    if len(y) < 10:
        return {'ct': float(len(y)), 'confidence': 0.0, 'method': 'fallback', 'r2_fit': 0.0}

    bl_region = y[2:8]
    bl_mean, bl_std = np.mean(bl_region), np.std(bl_region)
    y_corr = y - bl_mean
    y_max = np.max(y_corr)
    threshold = max(10 * bl_std, 0.12 * y_max, 600.0)

    results = {}

    # 1. Threshold
    crosses = np.where(y_corr > threshold)[0]
    if len(crosses) > 0:
        idx = crosses[0]
        if idx > 0:
            y1, y2 = y_corr[idx-1], y_corr[idx]
            results['threshold'] = idx - 1 + (threshold - y1) / (y2 - y1)

    # 2. Cy0
    r2 = 0.0
    try:
        p0 = [y_max, 1.0, len(x)/2, np.min(y_corr)]
        bounds = ([0, 0.1, 5, -np.inf], [np.inf, 5.0, 35, np.inf])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", OptimizeWarning)
            popt, _ = curve_fit(sigmoid_4pl, x, y_corr, p0=p0, bounds=bounds, maxfev=20000)
        results['cy0'] = popt[2] - 1.0 / popt[1]
        ss_res = np.sum((y_corr - sigmoid_4pl(x, *popt))**2)
        ss_tot = np.sum((y_corr - np.mean(y_corr))**2)
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    except Exception:
        pass

    # 3. 2nd Derivative Max
    try:
        y_smooth = savgol_filter(y_corr, window_length=7, polyorder=3)
        d2 = np.gradient(np.gradient(y_smooth))
        d2_max_idx = np.argmax(d2[5:-5]) + 5
        results['deriv2'] = float(d2_max_idx)
    except Exception:
        pass

    # Hibrit karar
    ct_val = results.get('cy0', results.get('threshold', results.get('deriv2', float(len(x)))))
    used_method = 'cy0' if 'cy0' in results else ('threshold' if 'threshold' in results else 'deriv2')

    # MIQE Güvenilirlik Skoru
    confidence = 0.0
    if r2 > 0.98: confidence += 0.4
    try:
        mask = (y_corr > 0.05 * y_max) & (y_corr < 0.30 * y_max)
        if np.sum(mask) >= 4:
            slope, _ = np.polyfit(x[mask], np.log10(y_corr[mask]), 1)
            eff = 10**(-1/slope) - 1
            if 0.85 <= eff <= 1.05: confidence += 0.3
    except Exception: pass
    if bl_std < 0.05 * y_max: confidence += 0.3
    confidence = min(1.0, confidence)

    if ct_val < 5.0 or ct_val > 38.0:
        ct_val = results.get('threshold', ct_val)
        used_method = 'threshold_fallback'
        confidence *= 0.5

    return {
        'ct': max(5.0, min(ct_val, float(len(x)))),
        'confidence': round(confidence, 2),
        'method': used_method,
        'r2_fit': round(r2, 3),
        'details': results
    }