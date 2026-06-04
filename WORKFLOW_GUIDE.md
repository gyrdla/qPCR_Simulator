# 🧬 qPCR Simulator v2.1 – İş Akışı & Modül Bağımlılık Haritası

## 🔗 TEMEL AKIŞ (Zorunlu Sıra)

🧬 Sekans & Primer
│
▼
⚙️ Reaksiyon & Döngü ←─── (Opsiyonel: 🎨 Multiplex)
│
▼
📊 Plaka & Kuyu
│
▼
🚀 Başlat (Simülasyon)
│
▼
📊 Sonuçlar & Rapor ←─── (Otomatik Güncellenen Paneller)
├── 📈 ROC & LoQ
├── 📤 LIMS Export
└── 🧪 Senaryo Modu

## 🔍 PANEL BAĞIMLILIKLARI

| Panel | Gerektirdiği Ön Koşul | Ne Zaman Aktif Olur? | Çıktısı |
|-------|----------------------|---------------------|---------|
| `🧬 Sekans & Primer` | Yok | Her zaman | Primer sekansı, Tm, ΔG |
| `🔬 İzomorf & Spesifiklik` | Accession + Primer | Sekans girildikten sonra | Off-target tablosu, Dimer ΔG |
| `⚙️ Reaksiyon & Döngü` | Yok (ama primer önerilir) | Her zaman | Mg/Ta/Primer ayarları, Optimizasyon |
| `📊 Plaka & Kuyu` | Yok | Her zaman | Well dizilimi, edge factor |
| `🎨 Multiplex` | Yok | Her zaman | Kanal ataması (FAM/HEX/Cy5) |
| `🧪 Senaryo Modu` | Yok | Her zaman | Biyolojik varyasyon parametreleri |
| `🚀 Başlat` | 🧬 + ⚙️ + (📊 veya 🎨) | Tüm girişler dolduğunda | Simülasyon sonuçları |
| `📈 ROC & LoQ` | 🚀 Başlat (simülasyon bitmeli) | Simülasyon tamamlandığında **otomatik** | AUC, LoQ, ISO checklist |
| `📤 LIMS Export` | 🚀 Başlat (simülasyon bitmeli) | Simülasyon tamamlandığında **otomatik** | CSV/JSON + PDF/HTML |
| `📊 Sonuçlar & Rapor` | 🚀 Başlat | Simülasyon tamamlandığında | Grafik + Tablo + Metrikler |

## 🔄 VERİ AKIŞI (State Management)
[Input Panels]
│
▼
[SimulationWorker] → (Async) → [Results]
│ │
▼ ▼
[ProjectState.save()] [ROC/LIMS/Senario.update_data()]
│
▼
[reports/session_*.json] ← LIMS Export buradan okur

## 🚨 HATA YÖNETİMİ
- Tüm paneller `ErrorLogger` kullanır → Hatalar `./logs/error_*.log` dosyasına yazılır
- GUI asla çökmez → Kullanıcıya okunabilir mesaj + log dosya yolu gösterilir
- Traceback tam olarak kaydedilir → Geliştirici için debug kolaylığı

## 🧪 HIZLI TEST SENARYOSU (Adım Adım)
1. `🧬 Sekans & Primer` → Accession: `NM_000546.6` → Fetch → Fwd/Rev gir
2. `🔬 İzomorf & Spesifiklik` → Analyze → Tabloda `+/-` yön, ΔG riski gör
3. `⚙️ Reaksiyon & Döngü` → Optimize Et → Top-3 öneriyi not al
4. `📊 Plaka & Kuyu` → 4 kuyu tanımla → Aktar
5. `🎨 Multiplex` → FAM/HEX/Cy5 ata → Uygula *(opsiyonel)*
6. `🧪 Senaryo Modu` → FC:2.5, CV:0.12 → Simüle Et *(opsiyonel)*
7. `🚀 Başlat` → Loading → Sonuçlar sekmesi
8. `📈 ROC & LoQ` → AUC ≥0.95, CV ≤5% kontrol et *(otomatik güncellendi)*
9. `📤 LIMS Export` → CSV indir, `reports/` klasöründe PDF/HTML gör *(otomatik)*

✅ Tüm adımlar sorunsuz tamamlanırsa, v2.1 production-ready'dir.