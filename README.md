# qPCR Simulator
Gerçekçi, MIQE uyumlu, termodinamik ve kinetik temelli qPCR simülasyon aracı.  
Öğrenciler, araştırmacılar ve teknik optimizasyon için tasarlanmıştır.

##  Özellikler
- SantaLucia 1998 + Owczarzy 2008 Mg²⁺/dNTP düzeltmeli Tm/ΔG hesabı
- Hot-start lag, amplifiable fraction, substrat/ürün inhibisyonlu kinetik model
- SYBR/TaqMan optik profili, heteroscedastic PMT gürültüsü
- Hibrit Ct (Cy0 + 2nd Derivative + Threshold) + MIQE güvenilirlik skoru
- NCBI entegrasyonu + otomatik primer tasarımı
- Master Mix presetleri (SYBR, TaqMan, LC480)
- LC480/QuantStudio thermal profil + ramp/hold kinetik entegrasyonu
- Teknik/Biyolojik tekrar simülasyonu (Poisson, pipet CV%, blok uniformitesi)
- PNG/CSV export, thread-safe GUI

##  Kurulum
```bash
git clone <repo-url>
cd qPCR_Simulator
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
python main.py


Lisans & Atıf
Eğitim ve araştırma amaçlı açık kaynak. Yayınlarında kullanırsan lütfen repo linkini belirt.