# PRD: Kalite Güvence (QA), Veri Toplama ve Prompt Testi
**Sorumlu Rol:** Junior Prompt Tester & Veri Asistanı

## 1. Yönetici Özeti
Bu rol, yazılım ekibinin (Scraper, OCR, AI) geliştirdiği araçları "kırmak" için uğraşır (Stress Test). Ayrıca sistemin çalışması için gereken gerçek test verilerini (Altın Veri Seti) manuel olarak toplar ve doğruluğunu gözle kontrol eder. Demo günü olası bir felakette devreye girecek "Manuel Yedek Planı" (B Planı) bu kişinin sorumluluğundadır.

**Temel Hedef:** Geliştiricilere temiz test verisi sağlamak ve Demo günü sistemin %100 çalışacağından emin olmak.

## 2. Teknik Gereksinimler & Araçlar
* **Araçlar:** Web Tarayıcı, Excel/Google Sheets, VS Code (JSON düzenlemek için).
* **Yetkinlikler:** Dikkatli gözlem, detaycılık, temel JSON okuma bilgisi.
* **Sorumluluk Alanı:** `/data/test_cases/` klasörü.

## 3. Görev Tanımları ve İş Paketleri

### Görev A: "Altın Veri Seti" Oluşturma (Golden Dataset)
* **Amaç:** Scraper ve AI yazılmadan önce elde gerçek veri olması lazım.
* **Aksiyon:**
    1.  `Ticaret Sicil Gazetesi`ne gir. Rastgele veya bilinen büyük firmaları (Örn: THY, Aselsan, Mahalle Bakkalı Ltd. Şti.) arat.
    2.  Farklı senaryolara uygun 10 adet PDF indir ve şu formatta kaydet:
        * `case_01_clean.pdf` (Okunaklı, standart tablo)
        * `case_02_scanned.pdf` (Eski, silik, resim formatında - OCR'ı zorlamak için)
        * `case_03_complex.pdf` (Çok karışık sayfa yapısı olan)
    3.  Aynısını `İhale Yasaklısı` listesi için yap. Gerçekten yasaklı olan bir firma bul ve PDF'ini indir.

### Görev B: Doğruluk Kontrolü (Ground Truth Labeling)
* **Amaç:** AI'ın doğru söyleyip söylemediğini ölçmek.
* **Aksiyon:**
    1.  İndirdiğin 10 firma için bir Excel tablosu aç.
    2.  Sütunlara: `Firma Adı`, `Sermaye`, `Yönetici`, `Yasaklı mı?` yaz.
    3.  PDF'leri gözünle oku ve bu tabloyu manuel doldur.
    4.  **Kritik:** AI sistemi çalıştığında senin Excel'inle AI'ın ürettiği JSON aynı mı? Bunu kontrol et.

### Görev C: Prompt "Monkey Testing" (Sistemi Zorlama)
* **Amaç:** AI Orkestratörü (Üye 1) prompt yazdığında, modelin saçmalayıp saçmalamadığını test etmek.
* **Aksiyon:**
    1.  Sisteme mantıksız sorular veya girdiler ver.
        * *Örn:* Tarih yerine "Yarın" yaz.
        * *Örn:* Firma adı yerine "Çiçek Abbas" yaz (Böyle bir firma yoksa sistem ne yapıyor?).
    2.  Haber analizi için Google'dan hem çok iyi hem çok kötü haber metnini kopyala, sisteme ver. "Olumlu" habere "Olumsuz" diyor mu bak.

### Görev D: Demo Günü "B Planı" (Wizard of Oz)
* **Senaryo:** Demo sırasında internet kesildi veya Sicil Gazetesi sitesi çöktü.
* **Aksiyon:**
    1.  Daha önceden indirdiğin ve çalıştığından emin olduğun 3 firmanın tüm verilerini (PDF, JSON, Haber Metni) `demo_backup` klasörüne koy.
    2.  Yazılımcı arkadaşlarınla konuşup, koda "Eğer internet yoksa bu klasörden oku" modunu eklet.
    3.  Gerekirse Demo videosunu önceden ekran kaydı alarak hazırla.

## 4. Teslimatlar (Deliverables)
* [ ] `test_data/` klasörü içinde en az 10 farklı senaryo PDF'i.
* [ ] `validation_matrix.xlsx`: Hangi firmada hangi bilgi olması gerektiğinin manuel listesi.
* [ ] `bug_report.md`: "Şu PDF'te sermayeyi yanlış okudu", "Şu firmada hata verdi" gibi notların listesi.

## 5. Haftalık Plan

* [ ] **Gün 1:** Veri avcılığı. Sicil ve Resmi Gazete'de gezinip ilginç (zorlu) örnekler bulmak.
* [ ] **Gün 2:** Bulunan verilerin Excel'e işlenmesi (Doğrulama referansı için).
* [ ] **Gün 3:** Üye 3'ün OCR çıktılarını kontrol etme. "Bak burada 'Ş' harfini 'S' okumuş, düzeltin" geri bildirimi verme.
* [ ] **Gün 4:** Demo senaryosunun provasını yapma. Sistemin en hızlı çalıştığı firma ismini belirleme.

## 6. İpucu
* **Hata Bulmak İyidir:** "Sistem çalışmıyor" demekten çekinme. Senin görevin hatayı **şimdi** bulmak, jüri karşısında değil.
* **Logları Oku:** Sistem çalışırken arkada akan yazıları takip et, "Error" görürsen hemen Üye 1'e veya Üye 2'ye haber ver.
