# Michaelis-Menten + verimlilik decay modeli
import math
def polymerase_rate(dntp_conc: float, Vmax: float = 1.0, Km: float = 0.05) -> float:
    return Vmax * dntp_conc / (Km + dntp_conc)

def amplification_efficiency(cycle: int, E0: float = 0.95, k_decay: float = 0.02) -> float:
    """Plateau geçişi için üstel verimlilik düşüşü"""
    return max(E0 * math.exp(-k_decay * cycle), 0.01)

def amplify(F_prev: float, E: float, background: float = 0.0) -> float:
    return F_prev * (1 + E) + background