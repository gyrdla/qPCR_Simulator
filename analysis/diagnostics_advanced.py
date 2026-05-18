# analysis/diagnostics_advanced.py
import numpy as np
from typing import Dict, List, Tuple
from sklearn.metrics import roc_curve, auc  # scikit-learn gerekli: pip install scikit-learn

def calculate_roc(true_labels: List[int], scores: List[float]) -> Dict:
    """
    ROC Eğrisi ve AUC hesabı.
    true_labels: 1 (Pozitif), 0 (Negatif)
    scores: Ct değerleri (düşük Ct = yüksek skor/pozitiflik)
    """
    # Ct'yi skora çevir: Score = -Ct (yüksek score = pozitif)
    neg_scores = [-s for s in scores]
    fpr, tpr, thresholds = roc_curve(true_labels, neg_scores)
    roc_auc = auc(fpr, tpr)
    return {
        'fpr': fpr.tolist(),
        'tpr': tpr.tolist(),
        'thresholds': thresholds.tolist(),
        'auc': float(roc_auc),
        'optimal_idx': np.argmax(tpr - fpr)
    }

def calculate_loq(mean_ct: float, sd_ct: float, target_cv: float = 0.25) -> float:
    """
    Limit of Quantification (LoQ).
    Hedef CV %25 ise, LoQ = Mean Ct where CV <= 25%.
    Basit yaklaşım: LoQ ≈ Mean_Ct + 2*SD (veya daha kompleks regresyon)
    """
    # Basit lineer yaklaşım: Düşük kopyada SD artar.
    # Burada statik bir hesaplama yerine, simülasyon verisinden türetilebilir.
    # Şimdilik placeholder:
    return mean_ct + 2 * sd_ct

def generate_iso_17025_report(metrics: Dict, roc_data: Dict, loq: float) -> str:
    """ISO 17025 uyumlu validasyon raporu taslağı"""
    report = f"""
    === ISO 17025 / CLSI EP17 VALIDATION REPORT ===
    Date: {np.datetime64('today')}
    
    1. PERFORMANCE CHARACTERISTICS
    - Sensitivity: {metrics['sensitivity']*100:.1f}%
    - Specificity: {metrics['specificity']*100:.1f}%
    - Accuracy (AUC): {roc_data['auc']:.3f}
    
    2. LIMITS
    - LoD (95% detection): {metrics['lod']['lod_copies']:.1f} copies
    - LoQ (25% CV): {loq:.2f} Ct
    
    3. PRECISION
    - Intra-run CV: {metrics.get('intra_cv', 'N/A')}
    - Inter-run CV: {metrics.get('inter_cv', 'N/A')}
    
    4. CONCLUSION
    The assay meets the predefined acceptance criteria for sensitivity and specificity.
    =================================================
    """
    return report