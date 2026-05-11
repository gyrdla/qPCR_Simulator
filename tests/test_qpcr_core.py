# tests/test_qpcr_core.py
import pytest
import numpy as np
from core.thermodynamics import calculate_tm, calculate_delta_g
from core.simulation import run_qpcr_cycles
from core.reagents import ReactionMix
from analysis.ct_calculator import calculate_ct
from analysis.signal import generate_signal

class TestThermodynamics:
    def test_tm_range(self):
        seq = "AGCTGACCTGATCTTCAAGG"
        tm = calculate_tm(seq, primer_conc=250e-9, mg_mM=3.0, dntp_mM=0.2)
        assert 56.0 < tm < 60.0

    def test_delta_g_stability(self):
        seq = "AGCTGACCTGATCTTCAAGG"
        dg = calculate_delta_g(seq, temp_c=37.0)
        # 20-mer için literatür ΔG aralığı: -30 ~ -10 kcal/mol
        assert -30.0 < dg < -10.0

class TestKinetics:
    def test_curve_monotonicity(self):
        mix = ReactionMix(3.0, 0.2, 250.0, 1.0)
        curve = run_qpcr_cycles(1000, 40, mix, 58.0, 60.0)
        assert all(curve[i] <= curve[i+1] for i in range(len(curve)-1))

    def test_plateau_magnitude(self):
        mix = ReactionMix(3.0, 0.2, 250.0, 1.0)
        curve = run_qpcr_cycles(1000, 40, mix, 58.0, 60.0)
        assert curve[-1] > curve[0] * 1e5

class TestCtCalculator:
    def test_hybrid_ct_synthetic(self):
        x = np.arange(40)
        y = 300 + 10000 / (1 + np.exp(-0.8 * (x - 20))) + np.random.normal(0, 15, 40)
        res = calculate_ct(y.tolist(), method='hybrid')
        assert 18.0 < res['ct'] < 23.0
        assert res['confidence'] > 0.6
        assert res['r2_fit'] > 0.95

    def test_low_template_shift(self):
        x = np.arange(40)
        y = 300 + 2000 / (1 + np.exp(-0.7 * (x - 26))) + np.random.normal(0, 10, 40)
        res = calculate_ct(y.tolist(), method='hybrid')
        assert 24.0 < res['ct'] < 30.0

class TestSignal:
    def test_rfu_bounds(self):
        amp = [1000 * (1.9**i) for i in range(25)] + [1000 * (1.9**24)] * 15
        sig = generate_signal(amp, dye='SYBR')
        assert 200 < min(sig) < max(sig) < 15000
    