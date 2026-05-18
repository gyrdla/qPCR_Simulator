# test_specificity.py (Proje kök dizininde oluştur)
from ncbi.specificity import find_off_targets, calculate_mismatch_tm_penalty, simulate_melt_curve

genome = "ATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG"
primer = "ATCGATCGATCG"
hits = find_off_targets(primer, genome, max_mismatches=2)
print(f"Off-target hits: {len(hits)} | Risk dağılımı: {[h['risk'] for h in hits]}")

pen = calculate_mismatch_tm_penalty("AGCTTGGAAGGTCCTGTCTC", "AGCTTGGAAGGTCCTGTCTA")
print(f"SNP ΔTm penaltısı: {pen:.2f} °C")

melt = simulate_melt_curve("ATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG")
print(f"Melt Tm peak: {melt['tm_peak']:.2f} °C | GC: {melt['gc_content']}%")