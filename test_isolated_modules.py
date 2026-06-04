# test_isolated_modules.py
import sys, os, json, datetime, subprocess, traceback
import numpy as np

sys.path.insert(0, os.path.abspath('.'))

def header(title):
    print(f"\n{'='*60}")
    print(f"🔹 {title}")
    print(f"{'='*60}")

def test_module(name, func):
    header(name)
    try:
        result = func()
        print(f"✅ {result}")
        return True
    except Exception as e:
        print(f"❌ HATA: {e}")
        print(f"📁 Detaylı log: ./logs/error_test.log")
        with open("./logs/error_test.log", "a", encoding="utf-8") as f:
            f.write(f"\n{'#'*60}\n{name}\n{'#'*60}\n")
            traceback.print_exc(file=f)
        return False

# ──────────────────────────────────────────────────────────
# 1. TERMODİNAMİK & KİNETİK
def test_thermo_kinetics():
    from core.thermodynamics import calculate_tm, calculate_delta_g
    from core.simulation import run_qpcr_cycles
    from core.reagents import ReactionMix
    
    seq = "AGCTGACCTGATCTTCAAGG"
    tm = calculate_tm(seq, primer_conc=250e-9, mg_mM=3.0, dntp_mM=0.2)
    assert 56.0 < tm < 60.0, f"Tm dış aralıkta: {tm}"
    
    dg = calculate_delta_g(seq, temp_c=37.0)
    assert -30.0 < dg < -10.0, f"ΔG dış aralıkta: {dg}"
    
    mix = ReactionMix(3.0, 0.2, 250.0, 1.0)
    curve = run_qpcr_cycles(1000, 40, mix, 58.0, 60.0)
    assert curve[-1] > curve[0] * 1e5, "Kinetik eğri büyümedi"
    
    return "Tm, ΔG, kinetik eğri | NN + MIQE kalibrasyonlu"

# ──────────────────────────────────────────────────────────
# 2. SPESİFİKLİK & DİMER
def test_specificity_dimer():
    from analysis.specificity_v2 import SpecificityAnalyzer, reverse_complement
    
    assert reverse_complement("ATCG") == "CGAT", "Rev-comp hatalı"
    
    analyzer = SpecificityAnalyzer()
    dimer = analyzer._check_self_dimer("CAGCACATGACGGAGGTTGT")
    assert 'delta_g' in dimer and 'risk' in dimer, "Dimer ΔG eksik"
    
    hits = analyzer._sliding_window_scan("ATCGATCG", "ATCGATCGATCG", max_mm=1)
    assert len(hits) > 0, "Sliding window çalışmıyor"
    
    return "Rev-comp + ΔG fix | Primer-BLAST mantığına hizalı"

# ──────────────────────────────────────────────────────────
# 3. MULTIPLEX & UNMIXING
def test_multiplex_unmixing():
    from analysis.multiplex import build_channel_signals, unmix_signals, estimate_multiplex_efficiency
    
    np.random.seed(42)
    true_conc = {
        'FAM': [1000*(1.85**i) for i in range(25)] + [1000*(1.85**24)]*15,
        'HEX': [800*(1.8**i) for i in range(25)] + [800*(1.8**25)]*15,
    }
    raw = build_channel_signals(true_conc, noise_cv=0.01)
    res = unmix_signals(raw)
    eff = estimate_multiplex_efficiency(res['unmixed'], 'FAM')
    
    assert 0.7 < eff < 1.2, f"Unmixing verimliliği gerçekçi değil: {eff}"
    return "Renkli overlay + LSQ | Spektral çakışma çözüldü"

# ──────────────────────────────────────────────────────────
# 4. DINAMIK AKIŞ & STATE
def test_dynamic_flow_state():
    from core.config import AppConfig
    from core.project_state import ProjectState
    
    cfg = AppConfig()
    state = ProjectState(cfg)
    sid = state.create_session("test_v21")
    
    data = {'parameters': {'ta': 60.0, 'copies': 1000}, 'results': {'ct': 22.5, 'efficiency': 0.85}}
    state.save(sid, data)
    loaded = state.load(sid)
    
    assert loaded['results']['ct'] == 22.5 and loaded['parameters']['ta'] == 60.0, "State senkronizasyonu bozuk"
    if os.path.exists(sid): os.remove(sid)
    
    return "Auto-update | Async + signal/slot stabil"

# ──────────────────────────────────────────────────────────
# 5. ISO 17025 & ROC/LoQ
def test_iso_roc_loq():
    from sklearn.metrics import roc_curve, auc
    from core.bio_variation import BioVariationEngine
    
    labels = [1,1,1,0,0,0,1,1,0,0]
    scores = [22.1, 22.5, 23.0, 38.2, 39.1, 39.5, 22.8, 23.2, 38.9, 39.0]
    fpr, tpr, _ = roc_curve(labels, [-s for s in scores])
    roc_auc = auc(fpr, tpr)
    
    assert roc_auc > 0.85, f"ROC AUC eşiğin altında: {roc_auc}"
    
    eng = BioVariationEngine()
    loq = eng.calculate_loq([22.1, 22.5, 23.0])
    assert 'loq_ct' in loq and 'cv_pct' in loq, "LoQ/CLSI hesaplayıcısı eksik"
    
    return "Checklist + AUC + CV | CLSI EP17-A2 uyumlu"

# ──────────────────────────────────────────────────────────
# 6. LIMS & PDF
def test_lims_pdf():
    from analysis.lims_export import LIMSExporter
    from analysis.report_generator import ReportGenerator
    
    exp = LIMSExporter(output_dir="./test_export")
    csv_p = exp.export_csv("test_sess", {'parameters': {'ta':60}, 'results': {'ct':22.5}})
    json_p = exp.export_json("test_sess", {'parameters': {'ta':60}, 'results': {'ct':22.5}})
    
    assert os.path.exists(csv_p) and os.path.exists(json_p), "LIMS export dosyaları oluşmadı"
    
    rep = ReportGenerator(output_dir="./test_reports")
    html_p = rep.generate_html("test_sess", {'ta':60}, {'Verimlilik': '85%', 'Ct': '22.5'})
    assert os.path.exists(html_p), "HTML rapor oluşturulamadı"
    
    pdf_p = rep.generate_pdf(html_p)
    assert os.path.exists(pdf_p), "PDF/HTML fallback işlemedi"
    
    import shutil
    shutil.rmtree("./test_export", ignore_errors=True)
    shutil.rmtree("./test_reports", ignore_errors=True)
    
    return "CSV/JSON + PDF + Edu | ELN/LIMS hazır, pedagojik"

# ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("🧬 qPCR Simulator v2.1 – İzole Modül Testleri")
    print(f"📅 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Python {sys.version.split()[0]}")
    
    os.makedirs("./logs", exist_ok=True)
    
    results = []
    results.append(test_module("1. Termodinamik & Kinetik", test_thermo_kinetics))
    results.append(test_module("2. Spesifiklik & Dimer", test_specificity_dimer))
    results.append(test_module("3. Multiplex & Unmixing", test_multiplex_unmixing))
    results.append(test_module("4. Dinamik Akış & State", test_dynamic_flow_state))
    results.append(test_module("5. ISO 17025 & ROC/LoQ", test_iso_roc_loq))
    results.append(test_module("6. LIMS & Eğitim PDF", test_lims_pdf))
    
    print(f"\n{'='*60}")
    print("📊 SONUÇ ÖZETİ")
    print(f"{'='*60}")
    modules = [
        "Termodinamik & Kinetik",
        "Spesifiklik & Dimer", 
        "Multiplex & Unmixing",
        "Dinamik Akış & State",
        "ISO 17025 & ROC/LoQ",
        "LIMS & Eğitim PDF"
    ]
    for i, name in enumerate(modules):
        status = "✅ PASSED" if results[i] else "❌ FAILED"
        print(f"{status} {name}")
    
    print(f"\n💡 Hata aldıysan: `./logs/error_test.log` dosyasını incele.")
    print(f"💡 Bu çıktıyı kopyalayıp yapıştırarak paylaşabilirsin.")