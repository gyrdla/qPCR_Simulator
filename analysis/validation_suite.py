# analysis/validation_suite.py
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from typing import Dict, List, Tuple
from core.simulation import run_qpcr_cycles
from core.reagents import ReactionMix
from analysis.ct_calculator import calculate_ct
from analysis.signal import generate_signal
import datetime, os

class ValidationSuite:
    """
    İn siliko qPCR validasyon paketi.
    - 10x seri dilüsyon eğrisi (teorik slope: -3.32)
    - Verimlilik vs Mg²⁺ / Ta taraması
    - Otomatik PDF rapor (MIQE metrikleri, grafikler, hata bayrakları)
    """
    def __init__(self, base_params: Dict):
        self.base = base_params

    def _run_single(self, copies: float, mg: float, dntp: float, ta: float, tm: float, cycles: int) -> Tuple[float, float]:
        mix = ReactionMix(mg, dntp, self.base.get('primer_uM', 250.0), self.base.get('polymerase_U', 1.0))
        amp = run_qpcr_cycles(copies, cycles, mix, tm, ta, time_factor=self.base.get('time_factor', 1.0))
        sig = generate_signal(amp, dye=self.base.get('dye', 'SYBR'))
        res = calculate_ct(sig, method='hybrid')
        
        y = np.array(amp)
        y_max = np.max(y)
        mask = (y > 0.05*y_max) & (y < 0.30*y_max)
        eff = 0.90
        if np.sum(mask) >= 4:
            slope, _ = np.polyfit(np.arange(len(y))[mask], np.log10(y[mask]), 1)
            eff = 10**(-1/slope) - 1 if slope != 0 else 0.90
        return res['ct'], max(0.70, min(eff, 1.10))

    def run_dilution_series(self, copies_list: List[float] = None) -> Dict:
        if copies_list is None:
            copies_list = [1e6, 1e5, 1e4, 1e3, 1e2, 1e1]
        cts, effs = [], []
        for c in copies_list:
            ct, eff = self._run_single(c, self.base['mg'], self.base['dntp'], self.base['ta'], self.base['tm'], self.base['cycles'])
            cts.append(ct)
            effs.append(eff)
            
        log_c = np.log10(copies_list)
        valid = ~np.isnan(cts)
        if np.sum(valid) < 3:
            return {'error': 'Yeterli valid Ct değeri üretilemedi.'}
            
        slope, intercept = np.polyfit(log_c[valid], np.array(cts)[valid], 1)
        ss_res = np.sum((np.array(cts)[valid] - (slope*log_c[valid] + intercept))**2)
        ss_tot = np.sum((np.array(cts)[valid] - np.mean(np.array(cts)[valid]))**2)
        r2 = 1 - ss_res/ss_tot if ss_tot > 0 else 0.0
        eff_mean = 10**(-1/slope) - 1
        
        return {
            'copies': copies_list, 'cts': cts, 'effs': effs,
            'slope': slope, 'intercept': intercept, 'r2': r2,
            'efficiency': eff_mean, 'valid_points': int(np.sum(valid))
        }

    def run_parameter_scan(self, param_name: str, values: List[float]) -> Dict:
        results = []
        for v in values:
            mg = v if param_name == 'mg' else self.base['mg']
            ta = v if param_name == 'ta' else self.base['ta']
            ct, eff = self._run_single(self.base['copies'], mg, self.base['dntp'], ta, self.base['tm'], self.base['cycles'])
            results.append({'value': v, 'ct': ct, 'efficiency': eff})
        return {'param': param_name, 'scan': results}

    def generate_pdf_report(self, dil_res: Dict, scan_res: Dict = None, output_path: str = "qPCR_Validation_Report.pdf"):
        with PdfPages(output_path) as pdf:
            plt.figure(figsize=(8, 10))
            plt.suptitle("qPCR İn Siliko Validasyon Raporu", fontsize=14, fontweight='bold')
            
            # 1. Dilüsyon Eğrisi
            plt.subplot(3, 1, 1)
            valid = ~np.isnan(dil_res['cts'])
            plt.semilogx(dil_res['copies'], dil_res['cts'], 'o-', label='Simüle Ct')
            if dil_res.get('slope'):
                log_c = np.log10(np.array(dil_res['copies'])[valid])
                fit = dil_res['slope']*log_c + dil_res['intercept']
                plt.semilogx(np.array(dil_res['copies'])[valid], fit, '--r', label=f'Fit (R²={dil_res["r2"]:.3f})')
            plt.gca().invert_xaxis()
            plt.ylabel("Ct")
            plt.title("10x Seri Dilüsyon Eğrisi")
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            # 2. Verimlilik & MIQE Metrikleri
            plt.subplot(3, 1, 2)
            plt.axis('off')
            eff_pct = dil_res.get('efficiency', 0)*100
            miqe_pass = "✅ PASS" if (0.90 <= dil_res.get('efficiency',0) <= 1.10 and dil_res.get('r2',0) > 0.98) else "⚠️ FAIL"
            txt = (f"Slope: {dil_res.get('slope',0):.3f} (İdeal: -3.32)\n"
                   f"Verimlilik: {eff_pct:.1f}% (MIQE: %90-110)\n"
                   f"R²: {dil_res.get('r2',0):.4f} (MIQE: >0.98)\n"
                   f"MIQE Durumu: {miqe_pass}\n"
                   f"Tarih: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
            plt.text(0.1, 0.5, txt, fontsize=11, va='center', bbox=dict(facecolor='whitesmoke', alpha=0.5))
            
            # 3. Parametre Taraması (varsa)
            if scan_res:
                plt.subplot(3, 1, 3)
                vals = [r['value'] for r in scan_res['scan']]
                effs = [r['efficiency']*100 for r in scan_res['scan']]
                plt.plot(vals, effs, 's-', color='purple')
                plt.axhspan(90, 110, color='green', alpha=0.1, label='MIQE Aralığı')
                plt.xlabel(f"{scan_res['param'].upper()} Değeri")
                plt.ylabel("Verimlilik (%)")
                plt.title(f"Verimlilik vs {scan_res['param'].upper()} Taraması")
                plt.legend()
                plt.grid(True, alpha=0.3)
                
            plt.tight_layout()
            pdf.savefig()
            plt.close()
        return os.path.abspath(output_path)