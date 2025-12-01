# PRD: Arayüz Geliştirme ve Sistem Entegrasyonu
**Sorumlu Rol:** Arayüz & Entegrasyon Geliştirici

## 1. Yönetici Özeti
Bu rol, son kullanıcının (ve Jürinin) sistemle etkileşime girdiği Web Arayüzünü tasarlar. Arka planda çalışan karmaşık AI ve Scraping işlemlerini (Orkestratör'den gelen verileri) basit, anlaşılır ve şık bir panelde sunar.

**Temel Hedef:** Kullanıcıdan "Firma Adı" ve "Tarih" alıp, arka plandaki işlemleri bekletirken kullanıcıyı bilgilendirmek (Loading states) ve nihai raporu Markdown formatında görselleştirmek.

## 2. Teknik Gereksinimler & Kısıtlar
* **Dil:** Python 3.10+
* **Framework:** `Streamlit` (Hackathonlar için en hızlısı ve en stabili).
* **Görselleştirme:** Streamlit native componentleri (`st.markdown`, `st.metric`, `st.json`).
* **Çalışma Ortamı:** Localhost (Tarayıcı üzerinde çalışacak).

## 3. Geliştirilecek Ekranlar (UI Modules)

### Ekran A: Giriş Paneli (Sidebar veya Üst Kısım)
* **Girdi Alanları:**
    * `Firma Unvanı` (Text Input): Örn: "ABC Lojistik A.Ş."
    * `Tarih` (Date Picker): Raporun baz alınacağı tarih.
    * `Analizi Başlat` (Button): İşlemi tetikleyen buton.
* **Özellik:** Butona basıldığında diğer alanlar "disable" olmalı (çift tıklamayı önlemek için).

### Ekran B: İşlem Durumu (Progress Section)
* **Sorun:** AI ve Scraping işlemleri toplamda 30-60 saniye sürebilir. Kullanıcı dondu sanmamalı.
* **Çözüm:** `st.status` veya `st.spinner` kullanarak canlı log akışı sağlanmalı.
    * *Adım 1:* "Sicil Gazetesi taranıyor..." (Scraper çalışırken)
    * *Adım 2:* "PDF verileri işleniyor..." (OCR çalışırken)
    * *Adım 3:* "Yapay Zeka raporu yazıyor..." (LLM çalışırken)

### Ekran C: Rapor Çıktısı (Main Dashboard)
* **Özet Kartları (Metrics):**
    * Güven Skoru (Confidence Score): %85 (Yeşil/Sarı/Kırmızı renk kodu ile).
    * İncelenen Kaynak Sayısı: 3 Doküman.
    * Yasaklılık Durumu: "TEMİZ" (Yeşil Tık) veya "YASAKLI" (Kırmızı Çarpı).
* **Rapor Metni:**
    * Orkestratörden gelen Markdown metnini (`st.markdown`) render et.
* **Kaynaklar (Expanders):**
    * "Kaynakları Göster" açılır menüsü altında, raporda kullanılan PDF'lerin isimleri veya metin özetleri.

## 4. Entegrasyon Kontratı (Integration Contract)
*Orkestratör (Üye 1) sana `main.py` içinde bir `run_analysis(company, date)` fonksiyonu verecek. Sen bunu çağıracaksın.*

**Beklenen Yanıt (JSON):**
```json
{
  "status": "success", // veya "error"
  "data": {
    "report_markdown": "## Firma Özeti\nBu firma...",
    "metrics": {
      "confidence": 85,
      "source_count": 3,
      "is_banned": false
    },
    "evidence": [
      {"source": "Sicil Gazetesi", "content": "Sermaye: 100k TL..."},
      {"source": "Haberler", "content": "Olumlu haber..."}
    ]
  }
}
````

## 5\. Görev Listesi (Action Plan)

  * [ ] **Gün 1:** `Streamlit` ile "Merhaba Dünya" diyen, input alanları olan boş bir arayüz tasarlanması.
  * [ ] **Gün 2:** **Mock Data (Sahte Veri)** ile UI akışının kodlanması. (Arka plan çalışmadan, butona basınca 5 saniye bekleyip hazır bir JSON dosyasını ekrana basan kod).
  * [ ] **Gün 3:** Görsel İyileştirmeler. (Sayfa başlığı, Logo ekleme, Renkli metrikler).
  * [ ] **Gün 4:** **Gerçek Entegrasyon:** Üye 1'in yazdığı `run_analysis` fonksiyonunun UI içine gömülmesi.
  * [ ] **Gün 5:** Hata Yönetimi. (İnternet koparsa veya PDF bulunamazsa ekrana kırmızı hata mesajı basılması).

## 6\. Kritik Başarı Faktörü & İpuçları

  * **Demo Modu (Hile Butonu):** Hackathon'larda canlı demo bazen patlar (internet yavaşlar, site çöker). Kodun içine gizli bir "Demo Modu" koy. Örneğin firma adına "Demo\_Test" yazılırsa, hiç internete gitmeden önceden kaydedilmiş mükemmel bir raporu saniyesinde ekrana bas. Bu, sunumu kurtarır.
  * **State Management:** Streamlit her butona basıldığında sayfayı yeniler. `st.session_state` kullanarak raporun ekranda kalmasını sağla.
  * **Debug:** Sayfanın en altına `st.expander("Debug JSON")` koyup ham veriyi oraya yazdır. Geliştirirken hatayı bulmanı kolaylaştırır.

---

### Arayüzcü İçin Notlar (Sana Özel Tüyolar)
* **Kütüphane Seçimi:** Kesinlikle `Streamlit` kullanın. Flask veya Django ile uğraşmak bu kısa sürede zaman kaybıdır. Streamlit ile 50 satır kodda muazzam dashboardlar çıkar.
* **Renk Paleti:** Kurumsal bir hava vermek için koyu mavi/gri tonları veya Hackathon düzenleyen kurumun (KKB) renklerini (Mavi/Turuncu) kullanmak jürinin hoşuna gider.
