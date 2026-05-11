# ncbi/primer_design.py
from typing import List, Dict, Tuple
from core.thermodynamics import analyze_primer, calculate_delta_g

def _check_3prime_stability(seq: str) -> bool:
    """3' uç stabilitesi: son 5 bazın ΔG > -3.0 kcal/mol olmalı (non-spesifik uzamayı önler)"""
    if len(seq) < 5: return True
    tail = seq[-5:]
    dg = calculate_delta_g(tail, temp_c=37.0)
    return dg > -3.0

def _check_gc_clamp(seq: str) -> bool:
    """GC clamp: son 5 bazda 1-3 arası G/C olmalı (MIQE/Primer3 standardı)"""
    if len(seq) < 5: return True
    tail = seq[-5:]
    gc_count = sum(1 for b in tail if b in 'GC')
    return 1 <= gc_count <= 3

def design_primers(sequence: str, length_range: Tuple[int, int] = (18, 24),
                   gc_range: Tuple[float, float] = (40.0, 60.0),
                   tm_range: Tuple[float, float] = (58.0, 62.0),
                   max_self_dg: float = -3.0) -> List[Dict]:
    seq = sequence.upper().replace("\n", "").replace(" ", "").replace("\r", "")
    if len(seq) < 50:
        raise ValueError("Sekans çok kısa. Minimum 50 bp gerekli.")
        
    candidates = []
    for length in range(length_range[0], length_range[1] + 1):
        for i in range(len(seq) - length + 1):
            primer = seq[i:i+length]
            analysis = analyze_primer(primer, use_partition=False)
            
            if not (gc_range[0] <= analysis.gc_content <= gc_range[1]): continue
            if not (tm_range[0] <= analysis.tm <= tm_range[1]): continue
            if analysis.hairpin['has_hairpin']: continue
            
            dimer_pass = not analysis.dimer_self['has_dimer']
            if not dimer_pass and len(analysis.dimer_self.get('details', [])) > 0:
                dimer_pass = analysis.dimer_self['details'][0].get('dG_37', -10) > max_self_dg
            if not dimer_pass: continue
            
            if not _check_3prime_stability(primer): continue
            if not _check_gc_clamp(primer): continue
            
            candidates.append({
                'sequence': primer, 'start': i, 'length': length,
                'gc': round(analysis.gc_content, 1), 'tm': round(analysis.tm, 2),
                'dg_37': round(analysis.delta_g_37, 2)
            })
            
    # Aday yoksa TEK SEFERLİK gevşek tarama (recursion YOK)
    if not candidates and gc_range[0] > 35.0:
        return design_primers(sequence, length_range, (35.0, 65.0), (55.0, 65.0), -5.0)
        
    candidates.sort(key=lambda x: abs(x['tm'] - 60.0))
    return candidates[:10]

def find_primer_pairs(fwd_list: List[Dict], rev_list: List[Dict],
                      amplicon_range: Tuple[int, int] = (80, 200),
                      max_tm_diff: float = 2.0) -> List[Dict]:
    pairs = []
    comp = {'A':'T','T':'A','G':'C','C':'G'}
    
    def _check_hetero_3prime(fwd_seq: str, rev_seq: str) -> bool:
        """3'-3' heterodimer kontrolü (4+ baz overlap riskli)"""
        f_tail = fwd_seq[-6:]
        r_tail_rc = ''.join(comp.get(b,'N') for b in reversed(rev_seq[-6:]))
        for k in range(4, min(len(f_tail), len(r_tail_rc)) + 1):
            if f_tail[-k:] == r_tail_rc[:k]:
                return False
        return True

    for fwd in fwd_list:
        for rev in rev_list:
            dist = rev['start'] - fwd['start']
            if dist <= 0 or not (amplicon_range[0] <= dist <= amplicon_range[1]): continue
            if abs(fwd['tm'] - rev['tm']) > max_tm_diff: continue
            if not _check_hetero_3prime(fwd['sequence'], rev['sequence']): continue
            
            pairs.append({
                'forward': fwd, 'reverse': rev, 'amplicon_size': dist,
                'tm_diff': round(abs(fwd['tm'] - rev['tm']), 2),
                'avg_tm': round((fwd['tm'] + rev['tm']) / 2, 2)
            })
            
    # Çift yoksa TEK SEFERLİK tolerans genişletme (recursion YOK)
    if not pairs and amplicon_range[0] > 60:
        return find_primer_pairs(fwd_list, rev_list, (60, 250), 3.5)
        
    pairs.sort(key=lambda x: x['tm_diff'])
    return pairs[:5]