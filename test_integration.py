# test_integration.py
from core.master_mix import get_preset, apply_preset_to_mix
from core.thermal_profile import LC480_STANDARD
from analysis.replicates import ReplicateSimulator

preset = get_preset("SYBR Green (Standart)")
mix_cfg = apply_preset_to_mix(preset)
time_factor = LC480_STANDARD.get_efficiency_time_factor(60.0)
print(f"LC480 Annealing Efektif Süre Faktörü: {time_factor:.3f}")

params = {
    'copies': 1000, 'mg': mix_cfg['mg_total_mM'], 'dntp': mix_cfg['dntp_total_mM'],
    'primer_uM': mix_cfg['primer_uM'], 'polymerase_U': mix_cfg['polymerase_U'],
    'ta': 60.0, 'tm': 58.0, 'cycles': 40, 'dye': mix_cfg['dye_type']
}
sim = ReplicateSimulator(params, n_technical=3, n_biological=2, pipette_cv=0.02, thermal_sd=0.3)
res = sim.run()
print(f"Mean Ct: {res['mean_ct']:.2f} ± {res['sd_ct']:.2f} | CV: {res['cv_pct']}% | MIQE Pass: {res['miqe_pass']}")