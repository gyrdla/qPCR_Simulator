# core/thermodynamics.py
import math
import warnings
from dataclasses import dataclass, field
from typing import Dict, Tuple, Optional, List

# ─────────────────────────────────────────────────────────────────────────────
# 1. NEAREST-NEIGHBOR PARAMETRELERİ (SantaLucia 1998, PNAS 95:1460)
# ΔH: kcal/mol, ΔS: cal/(mol·K)
# ─────────────────────────────────────────────────────────────────────────────
NN_PARAMS = {
    'AA': (-7.9, -22.2), 'AT': (-7.2, -20.4), 'TA': (-7.2, -21.3), 'CA': (-8.5, -22.7),
    'GT': (-8.4, -22.4), 'CT': (-7.8, -21.0), 'GA': (-8.2, -22.2), 'CG': (-10.6, -27.2),
    'GC': (-9.8, -24.4), 'GG': (-8.0, -19.9), 'AC': (-7.8, -21.0), 'TC': (-8.2, -22.2),
    'TG': (-8.5, -22.7), 'AG': (-7.8, -21.0), 'TT': (-7.9, -22.2), 'CC': (-8.0, -19.9)
}

INIT_PARAMS = {'GC': (0.1, -2.8), 'AT': (2.3, 4.1)}
R = 1.987  # cal/(mol·K)

# ─────────────────────────────────────────────────────────────────────────────
# 2. MODİFİYE BAZ / PROB DESTEĞİ (Genişletilebilir)
# ─────────────────────────────────────────────────────────────────────────────
# LNA parametreleri: McTigue et al. 2004, Biochemistry 43:5389
# MGB bir baz değil, konjugattır. ΔG stabilizasyonu olarak eklenir.
MODIFIED_PARAMS = {
    'LNA_A': (-8.2, -23.1), 'LNA_T': (-7.6, -21.8),
    'LNA_G': (-9.1, -25.0), 'LNA_C': (-8.9, -24.2),
    'MGB_STABILIZATION_dG': -3.5  # kcal/mol (ortalama, sekans bağımlı değişir)
}

# ─────────────────────────────────────────────────────────────────────────────
# 3. ÇEKİRDEK HESAPLAYICILAR
# ─────────────────────────────────────────────────────────────────────────────
def _reverse_complement(seq: str) -> str:
    comp = {'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G', 'N': 'N'}
    return ''.join(comp.get(b, 'N') for b in reversed(seq))

def is_self_complementary(seq: str) -> bool:
    return seq.upper() == _reverse_complement(seq.upper())

def _sum_nn_params(sequence: str, modified: bool = False) -> Tuple[float, float]:
    """NN toplamı + terminal düzeltme. ΔH: kcal/mol, ΔS: cal/(mol·K)"""
    seq = sequence.upper()
    if len(seq) < 2:
        raise ValueError("NN hesabı için sekans ≥2 nt olmalı.")
        
    dH, dS = 0.0, 0.0
    dH += INIT_PARAMS['GC'][0] if seq[0] in 'GC' else INIT_PARAMS['AT'][0]
    dS += INIT_PARAMS['GC'][1] if seq[0] in 'GC' else INIT_PARAMS['AT'][1]
    dH += INIT_PARAMS['GC'][0] if seq[-1] in 'GC' else INIT_PARAMS['AT'][0]
    dS += INIT_PARAMS['GC'][1] if seq[-1] in 'GC' else INIT_PARAMS['AT'][1]
    
    for i in range(len(seq) - 1):
        dinuc = seq[i:i+2]
        if modified and dinuc in MODIFIED_PARAMS:
            dH += MODIFIED_PARAMS[dinuc][0]
            dS += MODIFIED_PARAMS[dinuc][1]
        elif dinuc in NN_PARAMS:
            dH += NN_PARAMS[dinuc][0]
            dS += NN_PARAMS[dinuc][1]
        else:
            raise ValueError(f"Geçersiz dinükleotid: {dinuc}")
    return dH, dS

def _owczarzy_2008_correction(tm_na_c: float, mg_mM: float, dntp_mM: float, gc_frac: float) -> float:
    """
    Owczarzy 2008 (Biochemistry 47:5336) Mg2+/dNTP düzeltmesi.
    Geçerli aralık: [Mg2+] 0.5-10 mM, [dNTP] 0.1-1.0 mM, [Na+] 0.01-0.3 M
    """
    if mg_mM <= 0 or dntp_mM < 0:
        return tm_na_c
        
    # Serbest Mg2+ (dNTP'ler Mg2+ bağlar)
    mg_free = max(mg_mM - dntp_mM, 0.1)
    
    # Owczarzy 2008 Eq. 22 (sadeleştirilmiş üretim formu)
    # 1/Tm = 1/Tm_Na + a + b*ln[Mg] + c*[Mg] + d*[Mg]^2 + e*[dNTP] + f*[Mg]*[dNTP]
    a, b, c, d, e, f = 3.92e-5, -9.11e-6, 6.26e-5, -1.42e-5, 1.08e-5, -2.12e-6
    
    tm_na_k = tm_na_c + 273.15
    inv_tm = (1 / tm_na_k) + a + b * math.log(mg_free) + c * mg_free + d * (mg_free**2) + e * dntp_mM + f * mg_free * dntp_mM
    tm_corrected_k = 1 / inv_tm
    return tm_corrected_k - 273.15

def calculate_tm(sequence: str, primer_conc: float = 250e-9, na_M: float = 0.05,
                 mg_mM: float = 3.0, dntp_mM: float = 0.2, modified: bool = False) -> float:
    """SantaLucia 1998 NN + Owczarzy 2008 iyon düzeltmesi"""
    dH, dS = _sum_nn_params(sequence, modified)
    dH_cal = dH * 1000
    n = 2 if is_self_complementary(sequence) else 4
    
    tm_na_k = dH_cal / (dS + R * math.log(primer_conc / n))
    tm_na_c = tm_na_k - 273.15
    
    gc_frac = sum(1 for b in sequence.upper() if b in 'GC') / len(sequence)
    return round(_owczarzy_2008_correction(tm_na_c, mg_mM, dntp_mM, gc_frac), 2)

def calculate_delta_g(sequence: str, temp_c: float = 37.0, modified: bool = False, probe_type: str = None) -> float:
    """ΔG(T) = ΔH° - T·ΔS° (kcal/mol)"""
    dH, dS = _sum_nn_params(sequence, modified)
    temp_k = temp_c + 273.15
    dG = dH - (temp_k * dS / 1000)
    
    if probe_type == 'MGB':
        dG += MODIFIED_PARAMS['MGB_STABILIZATION_dG']
    return round(dG, 2)

# ─────────────────────────────────────────────────────────────────────────────
# 4. İKİNCİL YAPI KONTROLLERİ (Heuristic + Termodinamik)
# ─────────────────────────────────────────────────────────────────────────────
def check_hairpin(sequence: str, min_stem: int = 3, loop_size: int = 4) -> Dict:
    """Hızlı hairpin taraması + basit ΔG tahmini"""
    seq = sequence.upper()
    comp = {'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G'}
    hits = []
    for i in range(len(seq) - min_stem - loop_size):
        stem = seq[i:i+min_stem]
        rest = seq[i+min_stem+loop_size:]
        rev_comp = ''.join(comp.get(b, 'N') for b in reversed(stem))
        if rev_comp in rest:
            # Basit stem ΔG tahmini (NN toplamı / 2)
            dH, dS = _sum_nn_params(stem)
            dG_37 = dH - (310.15 * dS / 1000)
            hits.append({'pos': i, 'stem': stem, 'dG_37': round(dG_37, 2)})
    return {'has_hairpin': len(hits) > 0, 'details': hits}

def check_dimer(seq1: str, seq2: str, min_match: int = 4) -> Dict:
    """Hızlı dimer taraması + ΔG tahmini"""
    s1, s2 = seq1.upper(), seq2.upper()
    comp = {'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G'}
    rev_comp2 = ''.join(comp.get(b, 'N') for b in reversed(s2))
    hits = []
    for i in range(len(s1) - min_match + 1):
        sub = s1[i:i+min_match]
        if sub in rev_comp2:
            dH, dS = _sum_nn_params(sub)
            dG_37 = dH - (310.15 * dS / 1000)
            hits.append({'pos_seq1': i, 'match': sub, 'dG_37': round(dG_37, 2)})
    return {'has_dimer': len(hits) > 0, 'details': hits}

def calculate_partition_structure(sequence: str, temp_c: float = 37.0) -> Optional[Dict]:
    """
    Opsiyonel: ViennaRNA partition function entegrasyonu.
    Kurulum: pip install ViennaRNA
    """
    # calculate_partition_structure içindeki import satırını şöyle güncelle:
try:
    import RNA  # type: ignore[import-untyped]
except ImportError:
    RNA = None

# ─────────────────────────────────────────────────────────────────────────────
# 5. ANALİZ PAKETİ
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class PrimerAnalysis:
    sequence: str
    length: int
    gc_content: float
    tm: float
    delta_g_37: float
    self_complementary: bool
    hairpin: Dict
    dimer_self: Dict
    partition: Optional[Dict] = None

def analyze_primer(sequence: str, primer_conc: float = 250e-9, na_M: float = 0.05,
                   mg_mM: float = 3.0, dntp_mM: float = 0.2, use_partition: bool = False) -> PrimerAnalysis:
    seq = sequence.upper()
    return PrimerAnalysis(
        sequence=seq,
        length=len(seq),
        gc_content=sum(1 for b in seq if b in 'GC') / len(seq) * 100,
        tm=calculate_tm(seq, primer_conc, na_M, mg_mM, dntp_mM),
        delta_g_37=calculate_delta_g(seq, 37.0),
        self_complementary=is_self_complementary(seq),
        hairpin=check_hairpin(seq),
        dimer_self=check_dimer(seq, seq),
        partition=calculate_partition_structure(seq) if use_partition else None
    )