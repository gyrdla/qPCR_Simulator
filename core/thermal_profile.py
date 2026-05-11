# core/thermal_profile.py
from dataclasses import dataclass
from typing import List
import math

@dataclass
class ThermalStep:
    name: str
    temp_c: float
    hold_time_s: float
    ramp_rate_c_per_s: float = 2.5  # LC480/QuantStudio ortalaması

class ThermalProfile:
    def __init__(self, steps: List[ThermalStep]):
        self.steps = steps

    def get_effective_time_at_temp(self, target_temp: float, tolerance: float = 1.5) -> float:
        """Hedef sıcaklıkta (±tolerans) geçen efektif süreyi hesaplar (saniye)"""
        eff_time = 0.0
        for step in self.steps:
            if abs(step.temp_c - target_temp) <= tolerance:
                # Ramp süresi: önceki adımdan bu adıma geçiş (basitleştirilmiş)
                ramp_time = 1.5 / step.ramp_rate_c_per_s  # ~1.5°C yaklaşım mesafesi
                eff_time += max(0.0, step.hold_time_s - ramp_time)
        return eff_time

    def get_cycle_time_s(self) -> float:
        """Toplam döngü süresi (ramp + hold)"""
        total = 0.0
        for i, step in enumerate(self.steps):
            total += step.hold_time_s
            if i > 0:
                delta_t = abs(step.temp_c - self.steps[i-1].temp_c)
                total += delta_t / step.ramp_rate_c_per_s
        return total

    def get_efficiency_time_factor(self, ta_temp: float) -> float:
        """
        Annealing/Extension süresine bağlı verimlilik çarpanı.
        Kısa süre → düşük uzama, uzun süre → doygunluk (Michaelis zaman entegrasyonu)
        """
        t_eff = self.get_effective_time_at_temp(ta_temp, tolerance=2.0)
        # t_half ≈ 8-12 sn (standart amplicon uzama yarı ömrü)
        t_half = 10.0
        return 1.0 - math.exp(-t_eff / t_half)

# Varsayılan cihaz profilleri
LC480_STANDARD = ThermalProfile([
    ThermalStep("Denature", 95.0, 10.0, ramp_rate_c_per_s=4.5),
    ThermalStep("Anneal", 60.0, 20.0, ramp_rate_c_per_s=2.5),
    ThermalStep("Extend", 72.0, 15.0, ramp_rate_c_per_s=3.0)
])

QUANTSTUDIO_FAST = ThermalProfile([
    ThermalStep("Denature", 95.0, 3.0, ramp_rate_c_per_s=5.0),
    ThermalStep("Anneal_Extend", 60.0, 30.0, ramp_rate_c_per_s=4.0)
])