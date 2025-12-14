# 🔍 KKB Hackathon - StackOverflow

**Agentic AI** tabanlı, kapsamlı ve otomatik şirket risk analizi  sistemi.

## 🎯 Özellikler

Bu sistem, 4 farklı veri kaynağını tarayarak şirketler hakkında detaylı risk raporu oluşturur:

1.  **🚫 Yasaklı Listesi Kontrolü** (`tool_banned_check.py`)
    *   **Resmi Gazete** üzerinden güncel yasaklı listesi taraması.
    *   OCR (EasyOCR) ile PDF dökümanlarından veri çıkarma.
    *   SQLite tabanlı önbellekleme sistemi.

2.  **📢 Kamu İlanları & Konkordato** (`ilan_gov_service.py`)
    *   **ilan.gov.tr** üzerinden kamu ilanlarının taranması.
    *   **Konkordato**, İflas, Tasfiye ve Mahkeme kararlarının tespiti.
    *   Yüksek riskli durumlar için özel uyarı mekanizması.

3.  **📰 Haber Analizi** (`news_service.py`)
    *   **Google News** üzerinden son 2 yıllık haber arşivi taraması.
    *   Negatif haber tespiti ve duygu analizi.
    *   "Not Found" durumunda pozitif dil kullanımı (Hallucination prevention).

4.  **🏢 Ticaret Sicili** (`tobb_service.py`)
    *   **TOBB** entegrasyonu ile resmi şirket kayıtlarının doğrulanması.
    *   Sicil gazetesi ilanlarının takibi.

5.  **🤖 Agentic Workflow** (`orchestrator/`)
    *   **Lead Researcher**: Veri toplama, doğrulama ve konsolidasyon.
    *   **Reporting Analyst**: Finansal risk analizi ve PDF rapor yazımı.
    *   Sıralı (Sequential) görev yapısı ile garantili tool kullanımı.

6.  **📊 Dinamik Raporlama**
    *   Özelleştirilmiş PDF rapor çıktısı.
    *   Türkçe karakter uyumlu (Font sanitization).
    *   Streamlit tabanlı modern kullanıcı arayüzü.

## 🧠 Teknik Mimari ve Tasarım

Bu proje, modern **Agentic AI** prensipleri ve **Modüler Mikroservis** yaklaşımı ile tasarlanmıştır.

### 1. Genel Mimari Tasarımı
Sistem; Kullanıcı Arayüzü, Ajan Orkestrasyonu, Araçlar (Tools) ve Veri Servisleri olmak üzere 4 ana katmandan oluşur.

```mermaid
graph TD
    User([Kullanıcı]) -->|Web UI| Streamlit[Streamlit Arayüzü]
    Streamlit -->|Başlat| Orch[Orchestrator (CrewAI)]
    
    subgraph "Agentic Layer"
        Orch -->|Görev 1-4| Researcher[Lead Researcher Agent]
        Orch -->|Görev 5| Analyst[Reporting Analyst Agent]
        
        Researcher -->|Karar & Aksiyon| Tools[Agent Tools]
        Analyst -->|Konsolidasyon| PDF[PDF Generator]
    end
    
    subgraph "Service Layer"
        Tools -->|Döküman| Banned[Yasaklı Kontrolü (OCR)]
        Tools -->|Haber| News[Google News Service]
        Tools -->|Resmi Veri| TOBB[Ticaret Sicil (TOBB)]
        Tools -->|İlan| Ilan[Kamu İlanları]
    end
    
    Tools -->|Ham Veri| Researcher
    Analyst -->|Final Rapor| Streamlit
```

### 2. Agentic Mimari ve Karar Alma Süreci
Sistemde **Sequential Process (Sıralı İşlem)** mimarisi kullanılır. Her ajan kendi görevini tamamlayıp çıktısını bir sonraki ajana devreder.

*   **ReAct (Reasoning + Acting) Döngüsü:**
    Ajanlar sadece komut uygulamaz, karar verir. Örnek bir düşünce döngüsü:
    1.  *Gözlem:* Kullanıcı "X Şirketi"ni sordu.
    2.  *Düşünce:* "Önce bu şirketin yasaklı olup olmadığına bakmalıyım."
    3.  *Aksiyon:* `check_banned_tool` aracını çağır.
    4.  *Sonuç:* Yasaklı değil.
    5.  *Düşünce:* "Şimdi haberleri kontrol etmeliyim."

*   **Rol Dağılımı:**
    *   **Lead Researcher:** "Sahadaki Dedektif". Ham veriyi toplar, temizler ve doğrular.
    *   **Reporting Analyst:** "Masa başı Analist". Toplanan veriyi finansal bir perspektifle yorumlar ve nihai raporu yazar.

### 3. Modüler Kod Yapısı
Proje, her biri tek bir sorumluluğa sahip bağımsız modüllerden oluşur:

*   **`orchestrator/`**: Ajanların beyni. Görevler (`tasks.py`), roller (`agents.py`) ve araç tanımları (`tools.py`) burada bulunur.
*   **`services/` (Root)**: Dış dünya ile iletişim kuran servisler (`news_service.py`, `ilan_gov_service.py`). Bu servisler ajanlardan bağımsızdır, tek başlarına da çalışabilirler.
*   **`TOBB/`**: Ticaret Sicil Gazetesi entegrasyonu. Karmaşık captcha ve oturum işlemlerini yönetir.

### 4. Döküman Okuma ve OCR Stratejisi
Yasaklı listesi kontrolü (`tool_banned_check.py`), hibrit bir yaklaşım kullanır:

1.  **Text Layer Analizi:** Önce PDF'in metin katmanını okumaya çalışır (Hızlı ve Ucuz).
2.  **OCR Fallback (Görüntü İşleme):** Eğer metin katmanı bozuksa veya şirket ismi tablolarda resim olarak saklanmışsa, **EasyOCR** ve **OpenCV** devreye girer.
3.  **Fuzzy Matching:** OCR hatalarını tolere etmek için "RapidFuzz" kütüphanesi ile yaklaşık eşleşme (%85 benzerlik) aranır.
 
Bu projeyi kendi bilgisayarınızda (local) çalıştırmak için aşağıdaki adımları sırasıyla takip edin.
 
### 1. Ön Hazırlıklar
*   **Python 3.10+**: Sisteminizde Python'un yüklü olduğundan emin olun.
*   **Git**: Projeyi klonlamak için.
 
### 2. Projeyi İndirin
```bash
git clone https://github.com/yusufozdil/kkb-hackathon-agentic-ai.git
cd kkb-hackathon-agentic-ai
```
 
### 3. Sanal Ortam (Virtual Environment) Kurulumu
Bağımlılıkların çakışmaması için sanal ortam kullanmanız şiddetle önerilir.
```bash
# Mac / Linux
python3 -m venv venv
source venv/bin/activate
 
# Windows
python -m venv venv
.\venv\Scripts\activate
```
 
### 4. Kütüphanelerin Yüklenmesi
```bash
pip install -r requirements.txt
```
*Not: Playwright hatası alırsanız `playwright install` komutunu çalıştırmanız gerekebilir.*
 
### 5. Konfigürasyon (.env Dosyası)
Bu adım, **TOBB Ticaret Sicil** ve **KKB API** erişimi için kritiktir.
 
1.  `.env.example` dosyasının ismini `.env` olarak değiştirin (veya kopyalayın).
    ```bash
    cp .env.example .env
    ```
2.  `.env` dosyasını bir metin editörü ile açın ve aşağıdaki alanları doldurun:
 
    *   **KKB_API_KEY**: Kloudeks API anahtarınız.
    *   **TOBB_COOKIE_...**: Ticaret Sicil Gazetesi verilerini çekebilmek için giriş yapmış bir oturumun çerezlerine (cookies) ihtiyacınız var.
 
    **TOBB Çerezlerini Nasıl Alırsınız?**
    1.  [ticaretsicil.gov.tr](https://www.ticaretsicil.gov.tr) adresine gidin ve giriş yapın.
    2.  Tarayıcınızda Geliştirici Araçlarını (F12) açın.
    3.  **Application** (veya Storage) sekmesine gidin -> **Cookies**.
    4.  `atrsrv-101020155`, `atrsrv-101041123` ve `atrsrv-101041124` isimli çerezlerin değerlerini kopyalayıp `.env` dosyasındaki ilgili yerlere yapıştırın.
 
> **⚠️ Önemli:** Bu çerezlerin süresi belirli bir süre sonra dolar. Eğer "Login Problem" hatası alırsanız, bu adımı tekrarlayıp `.env` dosyasındaki çerezleri güncellemelisiniz.


## 💻 Kullanım

### Web Arayüzü (Streamlit) - Önerilen

Uygulamayı başlatmak için:

```bash
python 3.13 -m streamlit run app.py
```

Tarayıcınızda `http://localhost:8501` adresi açılacaktır.
1.  Şirket adını girin.
2.  Tarih aralığını seçin.
3.  "Analizi Başlat" butonuna basın.
4.  PDF raporunu indirin.


## 🏗️ Proje Mimarisi

```
├── app.py                  # Streamlit Arayüzü
├── main.py                 # Orchestrator Entry Point
├── pdf_generator.py        # Rapor PDF Oluşturucu
├── ihale_db.py            # SQLite Veritabanı Katmanı
├── tool_banned_check.py   # Yasaklı Liste Aracı
├── ilan_gov_service.py    # Kamu İlanları Servisi
├── news_service.py        # Haber Servisi
├── orchestrator/
│   ├── agents.py          # CrewAI Agent Tanımları
│   ├── tasks.py           # CrewAI Görev Tanımları (5 Adımlı Akış)
│   ├── tools.py           # Agent Tool Wrapper'ları
│   └── schemas.py         # Pydantic Modelleri
└── data/                   # Oluşturulan Raporlar ve Önbellek
```

## ⚠️ Önemli Notlar

- **Veri Tutarlılığı**: Bazen TOBB veya İlan servisleri yanıt vermeyebilir ("Login Failed" vb.). Sistem bu durumlarda hata vermez, raporda "Veri erişilemedi" notu düşerek analize devam eder.
- **Yasaklı Kontrolü**: `check_banned_status` aracı hem önbellek hem de canlı kaynakları (PDF) kontrol eder.
- **PDF Karakter**: Türkçe karakter sorunlarını önlemek için özel font sanitization mekanizması aktiftir.

## 👥 Ekip

**KKB Hackathon - StackOverflow Team**

- Yusuf Özdil
- Atahan Düryaz
- Barış Uzel
- Nika Golestani
- Tuba Aykan


