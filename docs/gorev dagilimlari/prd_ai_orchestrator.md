# PRD: AI Orkestrasyon ve LLM Yönetimi
**Sorumlu Rol:** AI Lead & Takım Kaptanı

## 1. Yönetici Özeti
Bu rol, projenin "Beyni"ni inşa eder. Kullanıcıdan gelen isteği (Firma Adı + Tarih) alır, alt araçları (Scrapers & Data Processors) tetikler, gelen verileri LLM'e (Açık Kaynak Model) yorumlatır ve nihai raporu oluşturur.

**Temel Hedef:** Girdileri alıp, halüsinasyon görmeden, kaynakçalı (citations) ve güven skorlu (confidence score) bir JSON/Markdown rapor üretmek.

## 2. Teknik Gereksinimler & Kısıtlar
* **Model:** Yerel (Local) çalışacak.
* **Altyapı:** `Ollama` üzerinden model sunumu.
* **Framework:** `CrewAI` (Tavsiye edilen) veya `LangChain`. Ajanların rol tabanlı yönetimi için CrewAI bu senaryoya daha uygundur.
* **Dil:** Python 3.10+
* **Yasaklar:** OpenAI, Anthropic, Google Gemini API kullanımı YASAKTIR.

## 3. Sistem Mimarisi (Agentic Workflow)

Sistem "Sıralı (Sequential)" bir akış izleyecektir:

1.  **Girdi:** Kullanıcı -> `{"company_name": "ABC Lojistik", "date": "2024-01-01"}`
2.  **Manager Agent (Orkestratör):** Görevi alır ve alt araçlara dağıtır.
3.  **Tools (Araçlar):** (Diğer ekip üyelerinin yazdığı fonksiyonlar buraya bağlanacak)
    * `TradeRegistryTool`: Sicil gazetesinden PDF indirip parse edilmiş JSON döner.
    * `BannedListTool`: İhale yasaklısı listesini kontrol eder.
    * `NewsSearchTool`: Haberleri tarar ve duygu analizi yapar.
4.  **Synthesis (Sentez):** LLM, araçlardan gelen JSON çıktılarını okur.
5.  **Çıktı:** Yapılandırılmış Final Raporu.

## 4. Geliştirilecek Ajanlar (Agents)

Aşağıdaki ajanların prompt'larını ve konfigürasyonlarını hazırlamalısın:

### Ajan 1: Baş Araştırmacı (Lead Researcher)
* **Rol:** Veri toplama araçlarını kullanmak ve ham veriyi doğrulamak.
* **Goal:** "ABC Lojistik firması hakkında Ticaret Sicil, İhale Yasaklısı ve Haber verilerini eksiksiz topla."
* **Backstory:** "Sen detaylara takıntılı, hata kabul etmeyen bir denetçisin. Sadece kanıtlı verilerle çalışırsın."

### Ajan 2: Raporlama Uzmanı (Reporting Analyst)
* **Rol:** Toplanan veriyi okuyup insan için özetlemek.
* **Goal:** "Toplanan verileri kullanarak profesyonel, finansal bir dille özet rapor yaz. Her iddia için kaynak (citation) belirt."
* **Backstory:** "Sen kıdemli bir finansal risk analistisin. Yöneticiler için net, kısa ve güvenilir raporlar yazarsın."

## 5. Veri Kontratları (Data Contracts)
*Diğer ekip üyeleriyle (Scraper & OCR) bu formatlarda anlaşmalısın. Onlar sana bu formatta veri dönmek ZORUNDA.*

**Beklenen Girdi (Tools Output):**
Diğer arkadaşların kodları (Tool) çalıştığında sana şu yapıda bir JSON dönmeli:
```json
{
  "trade_registry": {
    "found": true,
    "capital": "100.000 TL",
    "managers": ["Ahmet Yılmaz"],
    "raw_text_summary": "..."
  },
  "banned_status": {
    "is_banned": false,
    "details": null
  },
  "news_sentiment": {
    "positive_count": 2,
    "negative_count": 1,
    "summary": "Genel olarak olumlu..."
  }
}
```

**Üreteceğin Çıktı (Frontend İçin):**
Senin kodun (Main.py) çalışıp bittiğinde Frontend'e (Streamlit) şunu dönmeli:

```json
{
  "report_text": "## Firma Özeti\nABC Lojistik firması...\n\n### Sermaye Yapısı\n...",
  "confidence_score": 85,
  "sources": ["Ticaret Sicil Gazetesi Syf 133", "Resmi Gazete 18.11.2025"],
  "status": "SUCCESS"
}
```

## 6\. Prompt Mühendisliği (Örnek System Prompt)

Modelin halüsinasyon görmemesi için şu tarz bir System Prompt kullanmalısın:

> "Sen bir şirket istihbarat asistanısın. Sana verilen 'Bağlam (Context)' içindeki bilgiler dışında ASLA dışarıdan bilgi uydurma.
> Eğer bir bilgi (örneğin sermaye miktarı) verilen metinlerde yoksa, 'Bilgi bulunamadı' yaz.
> Rapor dilin Türkçe ve resmi olmalı.
> İhale yasaklısı olup olmadığını mutlaka vurgula."

## 7\. Görev Listesi (Action Plan)

  * [ ] **Gün 1:** `Ollama` kurulumu ve modelin yerel test edilmesi.
  * [ ] **Gün 1:** `CrewAI` iskelet projesinin oluşturulması (Boş tool'lar ile).
  * [ ] **Gün 2:** Ajan Prompt'larının (System Instructions) yazılması ve iyileştirilmesi.
  * [ ] **Gün 3:** Diğer üyelerden gelen `Tool` kodlarının (Python fonksiyonları) CrewAI içine entegre edilmesi.
  * [ ] **Gün 4:** "Çaylak" üyenin bulduğu test verileri ile sistemin zorlanması (Stress Test).
  * [ ] **Gün 5:** JSON çıktı formatının Frontendci ile teyit edilmesi.

## 8\. Kritik Başarı Faktörü

  * **Hız:** Modelin yanıt süresi 30-45 saniyeyi geçmemeli. Gerekirse daha küçük model (Llama-3.2-3B) kullanılarak sadece özetleme yaptırılmalı.
  * **JSON Hatası:** LLM bazen bozuk JSON üretir. `Pydantic` parser kullanarak çıktıyı mutlaka validate et.


---

### Orkestratör İçin Notlar (Sana Özel Tüyolar)
* **Mock Data (Sahte Veri):** Scraper ekibi işini bitirene kadar bekleme. Kodun içinde `return {"capital": "100.000"}` gibi sahte veri dönen fonksiyonlar yaz ve mimariyi bunlarla kur. Scraper bitince gerçek fonksiyonu bağlarsın.
* **Çaylak'ı Kullan:** Çaylak üyeye "Bana ABC firması hakkında 3 tane olumlu, 2 tane olumsuz haber metni bul ve bir dosyaya kaydet" de. Bu metinleri LLM promptlarını denerken kullanacaksın.
