# PRD: Veri İşleme ve OCR (Görüntü İşleme)
**Sorumlu Rol:** Veri İşleme & OCR Mühendisi

## 1. Yönetici Özeti
Bu rol, Scraper tarafından indirilen "Ham (Raw)" dosyaları işleyerek, LLM'in anlayabileceği "Yapılandırılmış (Structured)" metin veya JSON formatına dönüştürür.

**Temel Hedef:** PDF, Resim veya HTML yığınları içinden gürültüyü (reklamlar, sayfa numaraları, logolar) temizlemek ve sadece saf bilgiyi çıkarmak.

## 2. Teknik Gereksinimler & Kısıtlar
* **Dil:** Python 3.10+
* **Kütüphaneler (Açık Kaynak):**
    * **PDF (Metin Bazlı):** `pdfplumber` (Tablo çıkartımı için en iyisi) veya `PyMuPDF (fitz)` (Hız için).
    * **OCR (Görüntü Bazlı):** `PaddleOCR` (Türkçe karakter başarısı `Tesseract`'tan daha yüksektir ve GPU gerektirmez).
    * **Veri Yapıları:** `Pandas` (Tablo manipülasyonu için), `Pydantic` (Veri doğrulama için).
* **Yasaklar:** Google Vision API, Azure Document Intelligence vb. Bulut OCR servisleri YASAKTIR.

## 3. Geliştirilecek Modüller (Tools)

### Modül A: PDF Tablo Ayıklayıcı (`tool_pdf_parser.py`)
* **Girdi:** Ticaret Sicil Gazetesi PDF'i (Genelde sütunlu yapıdadır).
* **Görev:**
    1.  PDF'in metin katmanı var mı kontrol et (`pdfplumber` ile).
    2.  Varsa, sayfa düzenini (layout) koruyarak metni çıkar.
    3.  **Kritik:** Gazete 2-3 sütun olabilir. Satır satır okumak yerine sütun sütun okuma algoritmasını kur.
    4.  Özellikle "Sermaye", "Yönetim Kurulu", "Amaç ve Konu" başlıklarının altındaki metin bloklarını ayıkla.

### Modül B: OCR Motoru (`tool_ocr_engine.py`)
* **Girdi:** Taranmış (Scanned) PDF veya Resim dosyaları (Eski kayıtlar için).
* **Görev:**
    1.  Eğer Modül A metin bulamazsa devreye gir.
    2.  `PaddleOCR` kullanarak görüntüyü tarat.
    3.  Türkçe dil desteğini (`lang='tr'`) aktif et.
    4.  Çıkan metindeki OCR hatalarını (Örn: `1` yerine `l`, `Ş` yerine `S`) basit regex kurallarıyla temizle.

### Modül C: Yasaklı Listesi Ayrıştırıcı (`tool_banned_parser.py`)
* **Girdi:** Resmi Gazete "Çeşitli İlanlar" PDF'i.
* **Referans:** Dokümandaki örnek tablo yapısı .
* **Görev:**
    1.  Sayfadaki tabloları bul.
    2.  Tablo başlıklarında "YASAKLANAN GERÇEK VEYA TÜZEL KİŞİ" sütununu tespit et.
    3.  Satırları gezerek hedef firma ismini (fuzzy matching / benzerlik araması ile) kontrol et.
    4.  Eşleşme varsa "Yasaklama Süresi" ve "Kararı Veren Kurum" bilgilerini çek.

## 4. Veri Kontratları (Data Contracts)
*Senin çıktın, doğrudan AI Orkestratörü'ne (Üye 1) gidecek. Şu formatta olmalı:*

**Fonksiyon Çıktısı (Örnek):**
```json
{
  "doc_type": "trade_registry_gazette",
  "parsing_method": "pdfplumber", // veya "ocr"
  "content": {
    "raw_text": ".... (LLM'e verilecek temiz metin) ...",
    "tables": [
      {
        "header": ["Kurucu", "Pay Tutarı"],
        "rows": [["Ahmet Yılmaz", "50.000"], ["Mehmet Demir", "50.000"]]
      }
    ],
    "metadata": {
      "page_count": 5,
      "date": "2024-11-18"
    }
  }
}
````

## 5\. Görev Listesi (Action Plan)

  * [ ] **Gün 1:** Çaylak üyenin indirdiği örnek PDF'ler üzerinde `pdfplumber` denemeleri. Sütunlu yapıları (columnar layout) düzgün ayrıştırabiliyor mu?
  * [ ] **Gün 2:** `PaddleOCR` kurulumu ve Türkçe modelinin indirilmesi. (Dikkat: Model dosyaları büyüktür, önceden indirin).
  * [ ] **Gün 2:** İhale Yasaklısı PDF'lerindeki tabloları otomatik tanıyan kodun yazılması.
  * [ ] **Gün 3:** Temizlik (Regex) kurallarının yazılması (Örn: Fazla boşlukları sil, satır sonu tirelerini birleştir).
  * [ ] **Gün 4:** Scraper (Üye 2) ile entegrasyon: "İndirilen dosyayı otomatik al ve işle".

## 6\. Kritik Başarı Faktörü & İpuçları

  * **Tablo Kabusu:** PDF tabloları bazen çizgisiz olabilir. `pdfplumber`'ın `extract_table(vertical_strategy='text')` ayarlarıyla oynamanız gerekecek.
  * **Fuzzy Matching:** Firma ismi PDF'te "ABC Lojistik A.Ş." geçebilir ama arama "ABC Lojistik" olabilir. `thefuzz` kütüphanesi kullanarak %90 üzeri benzerlikleri kabul edin.
  * **Crop (Kırpma):** OCR çok yavaşsa, PDF'in sadece ilgili kısmını (header'lara bakarak) kesip (crop) OCR'a sokun. Tüm sayfayı taratmak 10 saniye, kırpılmış alanı taratmak 1 saniye sürer.


---

### Veri İşlemci İçin Notlar (Sana Özel Tüyolar)
* **Dokümandaki İpucu:** Proje dokümanında paylaşılan ekran görüntülerinde tabloların yapısı çok net. Kodunuzu geliştirirken bu görselleri referans alın. Örneğin, "TC Kimlik No" ve "Vergi No" sütunları yan yana. Kodunuz bu header'ları (başlıkları) arayarak tabloyu bulmalı.
* **Çaylak Desteği:** OCR sonuçlarını kontrol etmek zordur. Çaylak üyeye, OCR çıktısı ile orijinal PDF'i yan yana koyup "Okunabiliyor mu?" diye rastgele kontrol ettirin.
