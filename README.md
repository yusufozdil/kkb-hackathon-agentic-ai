# 🔍 KKB Hackathon - AI-Powered Due Diligence System

Şirketlerin risk analizini otomatik olarak yapan AI destekli bir due diligence sistemi.

## 🎯 Özellikler

- **🚫 Resmi Gazete Yasaklı Listesi**: OCR ile PDF tarama ve veritabanı önbellekleme
- **📰 Haber Analizi**: Google News üzerinden Türkçe haber tarama
- **🏢 Ticaret Sicili**: TOBB entegrasyonu ile şirket bilgileri
- **🤖 AI Agents**: CrewAI framework ile koordineli veri toplama ve analiz
- **🎨 Web Arayüzü**: Streamlit ile kullanıcı dostu GUI

## 📋 Gereksinimler

- Python 3.12+
- Ollama (gemma3:4b modeli)
- TOBB hesabı (opsiyonel, ticaret sicili için)

## 🚀 Kurulum

### 1. Projeyi İndir

```bash
git clone https://github.com/KULLANICIADI/kkb-hackathon-agentic-ai.git
cd kkb-hackathon-agentic-ai
```

### 2. Bağımlılıkları Yükle

```bash
pip install -r requirements.txt
```

### 3. Ollama Kurulumu

[Ollama'yı indir](https://ollama.ai) ve modeli çek:

```bash
ollama pull gemma3:4b
ollama serve
```

### 4. Ortam Değişkenleri (Opsiyonel)

TOBB entegrasyonu için `.env` dosyası oluştur:

```bash
TTS_EMAIL=your_email@example.com
TTS_PASSWORD=your_password
```

## 💻 Kullanım

### Web Arayüzü (Önerilen)

```bash
streamlit run app.py
```

Tarayıcınızda `http://localhost:8501` açılacak.

### Komut Satırı

```bash
python main.py --company "ACME Teknoloji" --start 20241101 --end 20241130
```

## 🏗️ Proje Yapısı

```
├── app.py                  # Streamlit GUI
├── main.py                 # Ana orchestrator
├── ihale_db.py            # SQLite veritabanı yönetimi
├── tool_banned_check.py   # Resmi Gazete PDF tarayıcı (OCR)
├── news_service.py        # Google News RSS entegrasyonu
├── tobb_service.py        # Ticaret Sicili entegrasyonu
├── orchestrator/
│   ├── agents.py          # CrewAI agent tanımları
│   ├── tasks.py           # AI görev tanımları
│   ├── tools.py           # Agent araçları
│   └── schemas.py         # Pydantic veri modelleri
└── data/
    ├── ihale_yasakli.db   # Yasak listesi önbelleği
    └── pdf_cache/         # İndirilen PDF'ler
```

## 🔧 Teknolojiler

- **AI Framework**: CrewAI, LangChain
- **LLM**: Ollama (Gemma 3 4B)
- **OCR**: EasyOCR, OpenCV
- **PDF**: PyMuPDF
- **Web**: Streamlit
- **Database**: SQLite

## ⚠️ Windows Uyumluluğu

Windows'ta çalıştırırken `SIGHUP` hatası alırsanız:

```python
# C:\Users\...\site-packages\crewai\events\types\system_events.py dosyasını düzenleyin
SIGHUP = getattr(signal, 'SIGHUP', signal.SIGTERM)
SIGTSTP = getattr(signal, 'SIGTSTP', signal.SIGTERM)
SIGCONT = getattr(signal, 'SIGCONT', signal.SIGTERM)
```

## 📊 Çıktı Formatı

```json
{
  "report_text": "Şirket risk analizi...",
  "is_banned": false,
  "confidence_score": 85,
  "sources": ["news", "gazette"],
  "status": "SUCCESS"
}
```

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit atın (`git commit -m 'Add amazing feature'`)
4. Push yapın (`git push origin feature/amazing-feature`)
5. Pull Request açın

## 📄 Lisans

Bu proje KKB Hackathon için geliştirilmiştir.

## 👥 Ekip

KKB Hackathon - Agentic AI Team

---

**⚡ Powered by CrewAI, Ollama & Streamlit**
