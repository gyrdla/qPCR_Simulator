# analysis/specificity_v2.py
import numpy as np
from typing import Dict, List

def reverse_complement(seq: str) -> str:
    comp = {'A':'T', 'T':'A', 'C':'G', 'G':'C', 'N':'N'}
    return ''.join(comp.get(b, 'N') for b in reversed(seq.upper()))

class SpecificityAnalyzer:
    def __init__(self):
        self.mm_penalties = {'A': {'A': -1.2, 'C': -1.5, 'G': -1.6, 'T': -0.8},
                             'T': {'A': -0.8, 'C': -1.6, 'G': -1.5, 'T': -1.2},
                             'C': {'A': -1.6, 'C': -1.2, 'G': -0.8, 'T': -1.5},
                             'G': {'A': -1.5, 'C': -0.8, 'G': -1.2, 'T': -1.6}}

    def analyze_primer_vs_transcripts(self, primer: str, transcripts: Dict[str, str], is_reverse: bool = False) -> List[Dict]:
        p_seq = reverse_complement(primer.upper()) if is_reverse else primer.upper()
        results = []
        for tid, seq in transcripts.items():
            matches = self._sliding_window_scan(p_seq, seq)
            for m in matches:
                results.append({
                    'transcript_id': tid, 'start_pos': m['pos'],
                    'mismatches': m['mm_count'], 'tail_mismatches': m['tail_mm'],
                    'delta_tm': self._calc_delta_tm(p_seq, m['aligned_seq']),
                    'risk': self._classify_risk(m['mm_count'], m['tail_mm']),
                    'aligned_seq': m['aligned_seq'], 'strand': '-' if is_reverse else '+'
                })
        # Dimer kontrolü (Fwd vs Rev)
        dimer = self._check_self_dimer(primer.upper())
        return sorted(results, key=lambda x: (x['risk'] != 'HIGH', x['mismatches'])), dimer

    def _sliding_window_scan(self, primer: str, target: str, max_mm: int = 3) -> List[Dict]:
        p_len, t_len = len(primer), len(target)
        hits = []
        if t_len < p_len: return hits
        p_arr = np.array(list(primer))
        for i in range(t_len - p_len + 1):
            window = target[i:i+p_len]
            mm = int(np.sum(p_arr != np.array(list(window))))
            if mm <= max_mm:
                tail_mm = int(np.sum(p_arr[-5:] != np.array(list(window[-5:]))))
                hits.append({'pos': i, 'mm_count': mm, 'tail_mm': tail_mm, 'aligned_seq': window})
        return hits

    def _calc_delta_tm(self, primer: str, target: str) -> float:
        dtm = 0.0
        for p, t in zip(primer, target):
            if p != t: dtm += self.mm_penalties.get(p, {}).get(t, -1.0)
        return round(dtm, 2)

    def _classify_risk(self, mm: int, tail_mm: int) -> str:
        if tail_mm > 0 or mm == 0: return 'HIGH'
        if mm == 1: return 'MEDIUM'
        return 'LOW'

    def _check_self_dimer(self, seq: str) -> Dict:
        # Basit 3' complementarity + ΔG tahmini
        rev = reverse_complement(seq)
        max_comp = 0
        for shift in range(len(seq)-3):
            comp = sum(1 for a, b in zip(seq[shift:], rev) if a == b)
            max_comp = max(max_comp, comp)
        delta_g = max_comp * -1.5  # kcal/mol approx
        return {'delta_g': delta_g, 'risk': 'HIGH' if max_comp >= 4 else ('MEDIUM' if max_comp >= 3 else 'LOW')}