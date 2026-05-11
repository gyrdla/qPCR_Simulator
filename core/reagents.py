# core/reagents.py
from dataclasses import dataclass

@dataclass
class ReactionMix:
    mg_total_mM: float
    dntp_total_mM: float
    primer_uM: float
    polymerase_U: float
    
    def get_free_mg(self) -> float:
        """Serbest Mg²⁺: dNTP ve dsDNA şelasyonu düşülür (literatür tabanlı)"""
        # dNTP'ler Mg²⁺ ile ~1:1 kompleks yapar (Kd ≈ 10⁻⁴ M)
        dntp_bound = self.dntp_total_mM * 0.92
        # dsDNA fosfat omurgası hafif Mg²⁺ bağlar
        dna_bound = max(0.0, (self.primer_uM / 1000.0) * 0.08)
        free = self.mg_total_mM - dntp_bound - dna_bound
        return max(0.15, free)  # Polimeraz aktivitesi için minimum eşik

    def update(self, amplicon_nM: float):
        """Döngü başı tükenme (substrat limitli plateau)"""
        # ~120 bp amplicon için ortalama nükleotid tüketimi
        consumption = amplicon_nM * 1e-6 * 0.12
        self.dntp_total_mM = max(0.01, self.dntp_total_mM - consumption)
        self.primer_uM = max(5.0, self.primer_uM - amplicon_nM * 1e-3)
        # Mg²⁺ tampon kapasitesi nedeniyle yavaş düşer
        self.mg_total_mM = max(0.8, self.mg_total_mM - consumption * 0.3)