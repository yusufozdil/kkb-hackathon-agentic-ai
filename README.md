# 🤖 KKB Hackathon - Agentic AI Due Diligence System

Şirket durum tespiti için yapay zeka destekli otonom araştırma sistemi.

## 📋 Özellikler

Sistem 3 ana veri kaynağından otomatik bilgi toplar:

1. **📰 Haber Taraması** - Google News RSS üzerinden Türkçe haber arama
2. **⚖️ İhale Yasaklı Kontrolü** - Resmi Gazete'den yasaklı firma taraması (OCR + DB)
3. **📄 Ticaret Sicil Gazetesi** - TOBB üzerinden şirket sicil kayıtları (OCR)

## 🚀 Kurulum

### 1️⃣ Repository'yi Klonlayın
```bash
git clone <repo-url>
cd kkb-hackathon-agentic-ai
```

### 2️⃣ Sanal Ortam Oluşturun (Önerilen)
```bash
# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3️⃣ Bağımlılıkları Yükleyin
```bash
pip install -r requirements.txt
```

### 4️⃣ Ortam Değişkenlerini Ayarlayın
```bash
# .env.example dosyasını .env olarak kopyalayın
cp .env.example .env

# .env dosyasını düzenleyin ve cookie'lerinizi ekleyin
```

**Cookie'leri Nasıl Alırsınız?**
1. Chrome/Firefox'ta [www.ticaretsicil.gov.tr](https://www.ticaretsicil.gov.tr)'ye gidin
2. Developer Tools açın (F12)
3. **Application** (Chrome) veya **Storage** (Firefox) > **Cookies** bölümüne gidin
4. `atrsrv-101041123` ve `atrsrv-101041124` cookie değerlerini kopyalayın
5. `.env` dosyasına yapıştırın

---

## 💻 Kullanım

### Temel Kullanım
```bash
python3 main.py --company "ŞİRKET ADI" --start YYYYMMDD --end YYYYMMDD
```

### Örnek
```bash
# ASELSAN için 1-5 Aralık 2025 tarihlerinde analiz
python3 main.py --company "ASELSAN" --start 20251201 --end 20251205
```

### Çıktılar
- **Console**: Detaylı log ve final JSON rapor
- **Dosya**: `reports/ŞIRKET_BAŞLANGIÇ_BİTİŞ_TIMESTAMP.json`

---

## 📁 Proje Yapısı

```
kkb-hackathon-agentic-ai/
├── main.py                    # Ana giriş noktası
├── orchestrator/              # AI agent orchestration
│   ├── agents.py             # Agent tanımları
│   ├── tasks.py              # Task tanımları
│   ├── tools.py              # Tool tanımları
│   └── schemas.py            # Pydantic şemaları
├── tool_banned_check.py      # Resmi Gazete yasaklı kontrolü
├── news_service.py           # Google News arama servisi
├── tobb_service.py           # TOBB entegrasyon servisi
├── ihale_db.py               # SQLite database yönetimi
├── TOBB/                     # TOBB web scraping modülleri
│   ├── TicaretScraper.py    # Şirket arama
│   ├── TTSClient.py         # İlan getirme & OCR
│   ├── TOBBOCR.py           # PDF OCR engine
│   └── mudurluk.json        # Ticaret sicil müdürlükleri
├── data/                     # Veri dosyaları
│   ├── ihale_yasakli.db     # Yasaklı şirketler DB
│   └── pdf_cache/           # PDF önbellek
├── reports/                  # Oluşturulan raporlar
├── requirements.txt          # Python bağımlılıkları
└── .env.example             # Ortam değişkenleri şablonu
```

---

## 🔧 Teknik Detaylar

### AI Orchestration
- **Framework**: CrewAI
- **Agents**: Lead Researcher, Reporting Analyst
- **Process**: Sequential (sıralı görev yürütme)

### Veri Kaynakları
1. **Resmi Gazete**: OCR ile PDF'den yasaklı firma çıkarma + SQLite cache
2. **Google News RSS**: Türkçe haber taraması (hl=tr&gl=TR)
3. **TOBB**: Cookie bypass ile ilan getirme + PyMuPDF OCR

### Cross-Platform Uyumluluk
- ✅ **Windows**: Poppler gerektirmez (PyMuPDF kullanıyor)
- ✅ **macOS**: Tam destek
- ✅ **Linux**: Tam destek

---

## 📊 Demo Hazırlığı

Demo gününde 5 farklı firma için rapor oluşturacaksınız:

### Toplu Test
```bash
# Şirket listesi
companies=("ASELSAN" "TÜRK HAVA YOLLARI" "GARANTİ BANKASI" "EREĞLI DEMİR ÇELİK" "TÜRK TELEKOMÜNİKASYON")

# Her biri için rapor oluştur
for company in "${companies[@]}"; do
    python3 main.py --company "$company" --start 20231201 --end 20251210
done
```

### Performans Logları
Sistem otomatik olarak şunları loglar:
- ✅ Her tool'un çalışma süresi
- ✅ Toplam rapor oluşturma süresi
- ✅ Bulunan kayıt sayıları

---

## ⚠️ Bilinen Sorunlar

### LLM Timeout
**Sorun:** Çok fazla ilan (405+) geldiğinde LLM timeout olabilir.

**Çözüm:** İlan sayısı otomatik 10 ile sınırlandırılmıştır (`tobb_service.py`).

### Cookie Expiration
**Sorun:** TOBB cookie'leri periyodik olarak expire olur.

**Çözüm:** Demoya yakın yeni cookie alın:
```bash
# Test edin
python3 -c "from dotenv import load_dotenv; import os; load_dotenv(); print('Cookie 1:', os.getenv('TOBB_COOKIE_1')[:20])"
```

### PDF OCR Yavaşlığı
**Sorun:** Büyük PDF'ler OCR'da yavaş.

**Çözüm:** Sistem 300 DPI kullanıyor, ihtiyaç halinde `TOBBOCR.py`'de `dpi=200` yapılabilir.

---

## 📚 API Referansı

### Tool 1: Check Banned Status
```python
{
  "company_name": "ASELSAN",
  "start_date": "20251201",  # YYYYMMDD
  "end_date": "20251205",
  "force_scan": false         # Optional: DB'yi bypass et
}
```

### Tool 2: Fetch News
```python
{
  "company_name": "ASELSAN",
  "start_date": "20251201",
  "end_date": "20251205",
  "limit": 50                 # Maksimum haber sayısı
}
```

### Tool 3: Fetch Trade Registry
```python
{
  "company_name": "ASELSAN",
  "start_date": "20251201",
  "end_date": "20251205"
}
```

---

## 🎯 Final Rapor Formatı

```json
{
  "report_text": "Türkçe risk analizi metni...",
  "is_banned": false,
  "confidence_score": 75,
  "sources": ["news", "gazette", "registry"],
  "status": "SUCCESS"
}
```

---

## 🛠️ Geliştirme

### Test
```bash
# Unit test (geliştirilecek)
pytest tests/

# Manuel test
python3 main.py --company "TEST" --start 20251210 --end 20251210
```

### Linting
```bash
# Kod kalitesi kontrolü
flake8 .
black .
```

---

## 📞 Destek

Sorunlar için:
1. `.env` dosyanızı kontrol edin
2. `pip install -r requirements.txt` yeniden çalıştırın
3. Cookie'leri yenileyin
4. Log dosyalarını inceleyin (`reports/` altında)

---

## 📄 Lisans

KKB Hackathon 2025 - Eğitim Amaçlı Proje

