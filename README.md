# qPCR Simulator v1.6
**First-principles kinetik/optik tabanlı, MIQE/IVD uyumlu in-silico qPCR dijital ikiz platformu.**

## 🎯 Kapsam & Dürüst Limitler (Scope & Disclaimer)
Bu sürüm (v1.6), **primer/kinetik/optik/multiplex seviyesinde** MIQE uyumlu bir ön-validasyon, optimizasyon ve eğitim simülatörüdür.  
✅ **Şu an desteklenenler:** SantaLucia/Owczarzy termodinamik, hot-start kinetik, first-principles optik (Beer-Lambert, PMT QE, shot noise), plate/ΔΔCt normalizasyon, CLSI EP17-A2 LoD, IVD cutoff, MIQE grid optimizasyon, **Multiplex LSQ Unmixing (FAM/HEX/Cy5)**, JSON/PNG/CSV export.  
⚠️ **Henüz modellenmeyenler:** Biyolojik ekspresyon varyasyonu, NCBI BLAST düzeyi off-target tarama, otomatik baseline drift düzeltme, ISO 17025 tam regülasyon raporu (taslak mevcut).  
🔬 **Klinik/IVD Uyarısı:** Bu araç laboratuvar validasyonunun yerine geçmez. Klinik tanı veya regülasyon başvuruları için ıslak lab validasyonu şarttır.

## 🧬 Özellikler
- **Termodinamik & Kinetik:** NN Tm/ΔG, Mg²⁺/dNTP şelasyonu, hot-start lag, amplifiable fraction, substrat/ürün inhibisyonu
- **First-Principles Optik:** Beer-Lambert + QY + filtre transmisyonu + PMT QE + shot/dark noise + menisküs + cihaz drift
- **Multiplex & Unmixing:** FAM/HEX/Cy5 overlap matrisi, LSQ dekonvolüsyon, quenching verimi, non-spesifik offset
- **Plate & Normalizasyon:** 8/12/96 editör, edge effect, NTC/REF/TARGET, ΔCt/ΔΔCt/Fold Change, geNorm M-value
- **Diagnostik & LoD:** Ct cutoff, Poisson dropout, CLSI LoD, Sens/Spec/FPR/FNR, IVD ready flag, ROC/AUC analizi
- **Optimizasyon:** Mg/Ta/Primer grid taraması, MIQE PASS top-3 öneri, laboratuvar yönlendirmesi
- **Spesifiklik & Melt:** k-mer off-target tarama, SNP ΔTm penaltısı, dsDNA melt curve simülasyonu
- **Yazılım:** Thread-safe PyQt6, responsive UI, pytest validasyon, PyInstaller `.exe`, JSON/PNG/CSV export

## 📥 Kurulum
```bash
git clone <repo-url>
cd qPCR_Simulator
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
python main.py