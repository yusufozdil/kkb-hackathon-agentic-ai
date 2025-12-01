# PRD: Web Otomasyon ve Veri Kazıma (Scraping)
**Sorumlu Rol:** Web Otomasyon Uzmanı

## 1. Yönetici Özeti
Bu rol, hedef web sitelerine (Ticaret Sicil Gazetesi, Resmi Gazete, Haber Kaynakları) programatik olarak erişen "Bot"ları yazar. Kullanıcı arayüzünden gelen "Firma Adı" ve "Tarih" bilgisini alıp, ilgili sitelerde arama yapar, sonuçları filtreler ve gerekli PDF/Metin dosyalarını indirerek yerel diske kaydeder.

**Temel Hedef:** Dış dünyaya kapalı veya zor erişilen verileri "Ham Dosya" (PDF/HTML) olarak sisteme indirmek.

## 2. Teknik Gereksinimler & Kısıtlar
* **Dil:** Python 3.10+
* **Ana Kütüphane:** `Playwright` (Selenium yerine tercih edilmeli, daha hızlı ve "headless" modda daha stabil).
* **Yedek Kütüphane:** `Requests` veya `BeautifulSoup` (Statik sayfalar için).
* **Veri Saklama:** İndirilen dosyalar `/data/raw/` klasörüne, metadata ise JSON olarak kaydedilmeli.
* **Hata Yönetimi:** Site cevap vermezse "Retry" (tekrar deneme) mekanizması olmalı.

## 3. Geliştirilecek Modüller (Tools)

### Modül A: Ticaret Sicil Botu (`tool_trade_registry.py`)
* **Hedef URL:** `https://www.ticaretsicil.gov.tr/`
* **Senaryo:**
    1.  Siteye login ol (Üyelik gerektiriyor, hackathon başında bir dummy hesap açılmalı).
    2.  "İlan Görüntüleme" sayfasına git.
    3.  Filtrelerden "Firma Unvanı"nı seç ve gelen parametreyi (Örn: "ABC Lojistik") yaz.
    4.  "Sicil Müdürlüğü" kısmını yönet (Genelde "Tümü" seçilmeli veya İstanbul/Ankara denenmeli).
    5.  Çıkan sonuçlardan en güncel olanın (veya istenen tarihe en yakın olanın) PDF butonuna tıkla ve indir.
* **Zorluk:** Login süreci ve Captcha çıkma ihtimali. (Çaylak üyeden manuel cookie alıp koda gömmek gerekebilir).

### Modül B: İhale Yasaklısı Botu (`tool_banned_check.py`)
* **Hedef URL:** `https://www.resmigazete.gov.tr/`
* **Senaryo:**
    1.  Sağ üst köşeden verilen "Tarih"i seç. 
    2.  Açılan sayfada "İLAN BÖLÜMÜ > Çeşitli İlanlar" başlığını bul ve tıkla. 
    3.  Açılan PDF veya HTML listesinde `CTRL+F` mantığıyla "İHALELERE KATILMAKTAN YASAKLAMA KARARI" başlığını ara. 
    4.  Bu başlık altındaki metinlerde veya tablolarda parametre olarak gelen "Firma Adı" geçiyor mu kontrol et.
* **Kritik:** Eğer firma ismi geçiyorsa o sayfanın PDF'ini indir.

### Modül C: Haber Tarama Botu (`tool_news_scraper.py`)
* **Hedef:** Google Search veya Google News.
* **Senaryo:**
    1.  `site:hurriyet.com.tr OR site:milliyet.com.tr "Firma Adı"` gibi bir sorgu at.
    2.  İlk 3-5 sonucun linkine git.
    3.  Sayfa içeriğini (HTML body text) çek. Reklamları ve menüleri temizle.
* **Not:** Google botları engellerse `DuckDuckGo` arama motoru kütüphanesi kullanılabilir.

## 4. Veri Kontratları (Data Contracts)
*Orkestratör (Üye 1) ve Veri İşlemci (Üye 3) senden bu çıktıları bekliyor.*

**Fonksiyon Çıktısı (Örnek):**
```python
def fetch_trade_registry_pdf(company_name):
    # ... işlemler ...
    return {
        "status": "success",
        "file_path": "./data/raw/sicil_gazetesi_2024.pdf",
        "metadata": {
            "download_date": "2025-11-28",
            "source_url": "..."
        }
    }
````

## 5\. Görev Listesi (Action Plan)

  * [ ] **Gün 1 (Sabah):** `Ticaret Sicil Gazetesi`ne üyelik açılması ve giriş yapıp PDF indiren basit bir Playwright scripti yazılması.
  * [ ] **Gün 1 (Öğle):** `Resmi Gazete` tarih seçici modülünün yazılması.
  * [ ] **Gün 2:** İndirilen dosyaların isimlendirme standardının (örn: `firmaadi_tarih_type.pdf`) ayarlanması.
  * [ ] **Gün 3:** Hata yakalama (Try-Except) bloklarının eklenmesi (Site açılmazsa program çökmesin, "Veri bulunamadı" desin).
  * [ ] **Gün 4:** Çaylak üyenin bulduğu zorlu firma isimleriyle test yapılması.

## 6\. Kritik Başarı Faktörü & İpuçları

  * **Session Yönetimi:** Sicil gazetesine her seferinde login olmak yerine, bir kere manuel girip `storage_state.json` (cookie dosyası) kaydedin. Playwright bu dosyayı okuyarak loginsiz devam edebilir.
  * **Bekleme Süreleri:** `time.sleep()` yerine Playwright'ın `page.wait_for_selector()` özelliğini kullanın. Hackathon interneti yavaş olabilir, sabit süreler hata verir.
  * **Headless Mod:** Geliştirirken `headless=False` yapın (tarayıcıyı görün), sunumda `headless=True` (arka planda çalışsın) yaparsınız.

---

### Web Otomasyoncusu İçin Notlar (Sana Özel Tüyolar)
* **Resmi Gazete Kolay Yolu:** Resmi Gazete URL yapısı genelde tahmin edilebilirdir (örn: `.../2025/11/20251118.htm`). Tarih seçiciyle uğraşmak yerine URL'i string formatlama ile (`f".../{yil}/{ay}/{yil}{ay}{gun}.htm"`) oluşturup direkt gitmek çok daha hızlıdır. [cite: 178]
* **Sicil Gazetesi:** Eğer bot yazmak çok zorlarsa (Captcha vs.), "Çaylak" üyeye Demo günü için 5 tane PDF indirtip klasöre koyun. Bot çalışıyormuş gibi o klasörden okutun. (Hackathon'da bazen "Wizard of Oz" taktiği hayat kurtarır).
