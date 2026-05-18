from analysis.multiplex import build_channel_signals, unmix_signals, estimate_multiplex_efficiency
import numpy as np

# 1. Gerçek konsantrasyon simülasyonu (FAM: hedef, HEX: ref, Cy5: iç kontrol)
cycles = 40
true_conc = {
    'FAM': [1000 * (1.85**i) for i in range(25)] + [1000 * (1.85**24)] * 15,
    'HEX': [800 * (1.80**i) for i in range(26)] + [800 * (1.80**25)] * 14,
    'Cy5': [500 * (1.75**i) for i in range(27)] + [500 * (1.75**26)] * 13
}

# 2. Cihazın ölçeceği ham sinyaller (crosstalk + noise + offset)
raw = build_channel_signals(true_conc, noise_cv=0.015, non_specific_offset=15.0)
print(f"Ham Ch1 (FAM filtresi) ilk 5: {[f'{v:.1f}' for v in raw['Ch1_FAM'][:5]]}")

# 3. LSQ Unmixing
res = unmix_signals(raw, non_specific_offset=15.0)
print(f"Unmixing Quality: {res['quality']} | Avg Residual: {res['avg_residual']:.2f}")

# 4. Verimlilik kontrolü
eff_fam = estimate_multiplex_efficiency(res['unmixed'], 'FAM')
eff_hex = estimate_multiplex_efficiency(res['unmixed'], 'HEX')
print(f"FAM E: {eff_fam*100:.1f}% | HEX E: {eff_hex*100:.1f}%")