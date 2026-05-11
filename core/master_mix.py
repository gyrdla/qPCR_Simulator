# core/master_mix.py
from dataclasses import dataclass, field
from typing import Dict

@dataclass
class MasterMixPreset:
    name: str
    mg_total_mM: float
    dntp_total_mM: float
    primer_uM: float
    polymerase_U: float
    dye_type: str
    probe_stabilization_dG: float = 0.0
    hotstart_lag_k: float = 0.45
    description: str = ""

# Ticari kit kalibrasyonları (üretici datasheet & MIQE ortalamaları)
PRESETS: Dict[str, MasterMixPreset] = {
    "SYBR Green (Standart)": MasterMixPreset(
        name="SYBR Green (Standart)",
        mg_total_mM=3.0, dntp_total_mM=0.2, primer_uM=250.0, polymerase_U=1.0,
        dye_type="SYBR", hotstart_lag_k=0.45,
        description="Genel amaçlı SYBR. 3 mM Mg, 0.2 mM dNTP, antikor hot-start."
    ),
    "SYBR Fast (High ROX)": MasterMixPreset(
        name="SYBR Fast (High ROX)",
        mg_total_mM=3.5, dntp_total_mM=0.25, primer_uM=300.0, polymerase_U=1.25,
        dye_type="SYBR", hotstart_lag_k=0.60,
        description="Hızlı döngü optimize. Yüksek Mg/dNTP, kısa annealing toleransı."
    ),
    "TaqMan Probe (FAM)": MasterMixPreset(
        name="TaqMan Probe (FAM)",
        mg_total_mM=4.0, dntp_total_mM=0.2, primer_uM=300.0, polymerase_U=1.0,
        dye_type="TaqMan", probe_stabilization_dG=-3.5, hotstart_lag_k=0.50,
        description="Prob bazlı. 4 mM Mg (prob bağlanma için), MGB/ZEN stabilizasyonu."
    ),
    "Roche LC480 Probes": MasterMixPreset(
        name="Roche LC480 Probes",
        mg_total_mM=3.8, dntp_total_mM=0.2, primer_uM=250.0, polymerase_U=1.0,
        dye_type="TaqMan", probe_stabilization_dG=-2.8, hotstart_lag_k=0.40,
        description="LightCycler 480 optimize. Düşük background, yüksek sinyal/gürültü."
    )
}

def get_preset(name: str) -> MasterMixPreset:
    if name not in PRESETS:
        raise ValueError(f"Bilinmeyen preset: {name}. Seçenekler: {list(PRESETS.keys())}")
    return PRESETS[name]

def apply_preset_to_mix(preset: MasterMixPreset) -> Dict:
    """Preset'i ReactionMix ve simülasyon parametrelerine dönüştürür"""
    return {
        'mg_total_mM': preset.mg_total_mM,
        'dntp_total_mM': preset.dntp_total_mM,
        'primer_uM': preset.primer_uM,
        'polymerase_U': preset.polymerase_U,
        'dye_type': preset.dye_type,
        'probe_stab_dG': preset.probe_stabilization_dG,
        'hotstart_lag_k': preset.hotstart_lag_k
    }