# ncbi/specificity.py
import numpy as np
from typing import List, Dict, Tuple

# Basit ama etkili k-mer + lokal hizalama tabanlı spesifiklik motoru
# Gerçek BLAST yerine in-silico hızlı tarama için optimize edilmiştir.

def reverse_complement(seq: str) -> str:
    comp = {'A':'T','T':'A','G':'C','C':'G','N':'N'}
    return ''.join(comp.get(b, 'N') for b in reversed(seq.upper()))

def find_off_targets(primer: str, genome_seq: str, max_mismatches: int = 2, min_match_len: int = 12) -> List[Dict]:
    """
    Primer'in hedef dışı bağlanma bölgelerini tarar.
    - k-mer ön filtreleme + sliding window mismatch sayımı
    - 3' uç mismatch'ları daha ağır penaltı alır (polimeraz uzama bloku)
    """
    primer = primer.upper()
    genome = genome_seq.upper()
    hits = []
    p_len = len(primer)
    
    for i in range(len(genome) - p_len + 1):
        window = genome[i:i+p_len]
        mismatches = sum(1 for a, b in zip(primer, window) if a != b)
        if mismatches <= max_mismatches:
            # 3' uç (son 5 baz) mismatch kontrolü
            tail_mm = sum(1 for a, b in zip(primer[-5:], window[-5:]) if a != b)
            penalty = mismatches + (tail_mm * 2.0)  # 3' uç 2x ağırlık
            if penalty <= max_mismatches + 1.5:
                hits.append({
                    'pos': i, 'seq': window, 'mismatches': mismatches,
                    'tail_mm': tail_mm, 'penalty': penalty,
                    'risk': 'YÜKSEK' if tail_mm >= 1 else ('ORTA' if mismatches >= 2 else 'DÜŞÜK')
                })
    return hits

def calculate_mismatch_tm_penalty(primer: str, target: str, mg_mM: float = 3.0) -> float:
    """
    SNP/mismatch ΔTm penaltısı (Wetmur 1991 + SantaLucia adaptasyonu)
    - Internal mismatch: ~-1.5°C / mismatch
    - 3' uç mismatch: ~-3.0°C / mismatch (uzama bloku)
    """
    mismatches = sum(1 for a, b in zip(primer.upper(), target.upper()) if a != b)
    tail_mm = sum(1 for a, b in zip(primer[-5:].upper(), target[-5:].upper()) if a != b)
    delta_tm = -(mismatches * 1.5) - (tail_mm * 1.5)
    return float(delta_tm)

def simulate_melt_curve(amplicon_seq: str, temp_range: Tuple[float, float] = (60.0, 95.0), steps: int = 70) -> Dict:
    """
    Basit dsDNA erime eğrisi simülasyonu (Marmur-Doty + GC içerik yaklaşımı)
    - Primer-dimer: kısa, düşük Tm peak'i
    - Spesifik ürün: uzun, yüksek Tm peak'i
    """
    seq = amplicon_seq.upper()
    gc = sum(1 for b in seq if b in 'GC') / len(seq)
    tm_approx = 64.9 + 41 * (gc - 0.16)  # Basit GC-based Tm
    
    temps = np.linspace(temp_range[0], temp_range[1], steps)
    # Sigmoid erime profili (dsDNA → ssDNA geçişi)
    fraction_ds = 1.0 / (1.0 + np.exp((temps - tm_approx) / 1.5))
    # Türev (dF/dT) → melt peak
    dF_dT = np.gradient(fraction_ds, temps)
    
    peak_idx = np.argmin(dF_dT)  # Negatif türev minimumu = erime noktası
    return {
        'temps': temps.tolist(),
        'fraction_ds': fraction_ds.tolist(),
        'derivative': dF_dT.tolist(),
        'tm_peak': float(temps[peak_idx]),
        'gc_content': round(gc * 100, 1)
    }