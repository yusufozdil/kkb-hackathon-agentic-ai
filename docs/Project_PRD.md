## 1. Yönetici Özeti (Executive Summary)
Bu proje, finansal kurumların veya işletmelerin, bir firma hakkında yapması gereken durum tespit (due diligence) süreçlerini otomatize eden **Otonom Ajan (Agentic AI)** sistemidir.

Sistem, sadece firma adı ve tarih bilgisi alarak; **Ticaret Sicil Gazetesi**, **İhale Yasaklısı Listeleri** ve **İnternet Haberlerini** tarar. Elde edilen verileri açık kaynaklı Yerel LLM (Büyük Dil Modelleri) ile analiz eder ve kullanıcıya kaynakçalı, güven skorlu, özet bir risk raporu sunar. Tüm süreç "Bulut API" kullanılmadan, tamamen yerel kaynaklarla gerçekleştirilir.

---

## 2. Problem Tanımı
Bir firmanın güvenilirliğini analiz etmek için analistlerin şu işlemleri manuel yapması gerekir:
1.  **Ticaret Sicil Gazetesi:** Karışık PDF'leri bulup, sermaye ve ortaklık yapılarını okumak.
2.  **Resmi Gazete:** Firmanın kamu ihalelerinden yasaklı olup olmadığını kontrol etmek.
3.  **Medya Taraması:** Firma hakkında çıkan haberleri okuyup itibar analizi yapmak.

Bu süreç yavaştır, hata yapmaya açıktır ve farklı formatlardaki (PDF, HTML, Resim) verilerin birleştirilmesini gerektirir.

---

## 3. Çözüm Mimarisi (Agentic Workflow)

Proje, **Orkestratör-İşçi (Manager-Worker)** mimarisi üzerine kuruludur.

* **Kullanıcı Arayüzü (Frontend):** Python Streamlit.
* **Orkestrasyon (Beyin):** CrewAI / LangChain.
* **LLM Motoru:** Karar verilecek.
* **Araçlar (Tools):**
    * `TradeRegistryScraper`: Ticaret sicil PDF indirme ve parse etme.
    * `BannedListScraper`: Resmi Gazete yasaklı sorgulama.
    * `NewsSentimentAnalyzer`: Haber tarama ve duygu analizi.

---

## 4. Temel Özellikler ve Gereksinimler

### 4.1. Fonksiyonel Gereksinimler
* **F01 - Parametrik Giriş:** Sistem, kullanıcıdan `Firma Adı` ve `Tarih` almalıdır.
* **F02 - Ticaret Sicil Analizi:** İlgili firmanın sicil gazetesi bulunmalı, PDF indirilmeli, "Sermaye", "Ortaklar" ve "Adres" bilgileri yapılandırılmış veri olarak çekilmelidir.
* **F03 - Yasaklılık Kontrolü:** Firmanın ihale yasaklısı olup olmadığı Resmi Gazete'den kontrol edilmelidir.
* **F04 - Haber Analizi:** Firma ile ilgili son haberler taranmalı ve "Olumlu/Olumsuz/Nötr" olarak sınıflandırılmalıdır.
* **F05 - Rapor Üretimi:** Toplanan tüm veriler, LLM tarafından yorumlanarak insan tarafından okunabilir bir özet rapor haline getirilmelidir.
* **F06 - Kaynak Gösterimi:** Rapordaki her bilgi, dayandığı belgeye (Citation) referans vermelidir.

### 4.2. Teknik Kısıtlar (Hackathon Kuralları)
* **Cloud API Yasağı:** OpenAI, Anthropic vb. API'lar kullanılamaz.
* **Açık Kaynak:** Sadece Open-Weights modeller (Llama, Mistral, Qwen) kullanılabilir.
* **Veri Gizliliği:** Kodlar Private Repo'da tutulmalıdır.

---

## 5. Teknik Teknoloji Yığını (Tech Stack)

| Katman | Teknoloji / Kütüphane | Amaç |
| :--- | :--- | :--- |
| **Frontend** | Streamlit | Hızlı ve interaktif kullanıcı arayüzü. |
| **Backend** | Python 3.10+ | Ana geliştirme dili. |
| **LLM Inference** | Ollama | Yerel modelleri API olarak sunmak. |
| **Model** | - | - |
| **Orkestrasyon** | CrewAI | Ajanların yönetimi ve görev dağılımı. |
| **Scraping** | Playwright | Dinamik web sitelerinden veri çekmek. |
| **PDF/OCR** | pdfplumber, PaddleOCR | PDF ve görüntülerden metin ayıklamak. |

---

## 6. Başarı Kriterleri (Success Metrics)
1.  **Doğruluk:** Sistemin "Sermaye 100.000 TL" dediği bilgi, indirilen PDF'te doğrulanabilmeli.
2.  **Tamamlanma:** 3 veri kaynağının (Sicil, Yasaklı, Haber) en az 2'sinden başarılı veri çekilebilmeli.
3.  **Performans:** Rapor oluşturma süresi **60 saniyenin altında** olmalı.
4.  **Dayanıklılık:** İnternet kesintisi veya veri bulunamaması durumunda sistem çökmemeli, "Bilgi bulunamadı" uyarısı vermeli.


---

## 7. Riskler ve B Planları

| Risk | Olasılık | Etki | B Planı (Mitigation) |
| :--- | :--- | :--- | :--- |
| **Sitelerin Captcha Sorması** | Yüksek | Kritik | Manuel cookie alıp koda gömmek veya önceden indirilmiş PDF'leri kullanmak. |
| **LLM'in Yavaş Çalışması** | Orta | Orta | 7B Model yerine 3B Model (Llama-3.2) kullanmak. |
| **PDF Formatının Değişmesi** | Orta | Yüksek | Sadece metin bazlı değil, OCR bazlı okuma yapmak. |
| **Demo Sırasında Hata** | Düşük | Kritik | Önceden hazırlanmış statik JSON çıktısını gösteren "Demo Modu"nu devreye almak. |

---

## 8. Ekip ve Rol Dağılımı
* **Üye 1 (Lead):** AI Orkestrasyon & Model Yönetimi.
* **Üye 2:** Web Otomasyon & Scraping.
* **Üye 3:** Veri İşleme & OCR.
* **Üye 4:** UI & Entegrasyon.
* **Üye 5:** QA, Veri Toplama & Test.
