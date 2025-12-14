from crewai import Task
from .schemas import RiskReport


class OrchestratorTasks:
    def check_banned_task(self, agent, company_name, start_date, end_date):
        return Task(
            description=(
                f"Step 1/4: Check Banned List for '{company_name}'.\n"
                f"You MUST call the 'Check Banned Status' tool with these exact parameters:\n"
                f"{{\"company_name\": \"{company_name}\", \"start_date\": \"{start_date}\", \"end_date\": \"{end_date}\", \"force_scan\": false}}\n\n"
                "If the tool returns found=true, note the details. If found=false, note that no ban was found.\n"
                "Do NOT do anything else. Do NOT call other tools."
            ),
            agent=agent,
            expected_output="A summary of the Banned Status check (Found/Not Found).",
        )

    def fetch_registry_task(self, agent, company_name, start_date, end_date):
        return Task(
            description=(
                f"Step 2/4: Fetch Trade Registry Data for '{company_name}'.\n"
                f"You MUST call the 'Fetch Trade Registry' tool with these exact parameters:\n"
                f"{{\"company_name\": \"{company_name}\", \"start_date\": \"{start_date}\", \"end_date\": \"{end_date}\"}}\n\n"
                "If it returns 'Login Failed' or 'Not Found', that is acceptable. Just document the result.\n"
                "Do NOT do anything else. Do NOT call other tools."
            ),
            agent=agent,
            expected_output="A summary of Trade Registry findings.",
        )

    def fetch_news_task(self, agent, company_name, start_date, end_date):
        return Task(
            description=(
                f"Step 3/4: Fetch News for '{company_name}'.\n"
                f"You MUST call the 'Fetch News' tool with these exact parameters:\n"
                f"{{\"company_name\": \"{company_name}\", \"start_date\": \"{start_date}\", \"end_date\": \"{end_date}\", \"limit\": 10}}\n\n"
                "This step is MANDATORY. You must execute the tool and retrieve the news items.\n"
                "Do NOT do anything else. Do NOT call other tools."
            ),
            agent=agent,
            expected_output="A summary of News findings (count of articles found).",
        )

    def fetch_announcements_task(self, agent, company_name, start_date, end_date):
        return Task(
            description=(
                f"Step 4/4: Fetch Public Announcements for '{company_name}'.\n"
                f"You MUST call the 'Fetch Public Announcements' tool with these exact parameters:\n"
                f"{{\"company_name\": \"{company_name}\", \"start_date\": \"{start_date}\", \"end_date\": \"{end_date}\", \"max_results\": 20}}\n\n"
                "This step is CRITICAL for legal risk (konkordato, bankruptcy).\n"
                "Do NOT do anything else. Do NOT call other tools."
            ),
            agent=agent,
            expected_output="A summary of Public Announcements findings.",
        )

    def consolidate_research_task(self, agent, company_name):
        return Task(
            description=(
                f"Step 5: Consolidate all research findings for '{company_name}'.\n"
                "Review the outputs from the previous 4 tasks (Banned, Registry, News, Announcements).\n"
                "Create a comprehensive summary that confirms all 4 tools were called.\n"
                "You do NOT need to call any tools here. Just aggregate the data from context."
            ),
            agent=agent,
            expected_output=(
                "MANDATORY CHECKLIST (START WITH THIS):\n"
                "✓ Banned Status: {STATUS}\n"
                "✓ Trade Registry: {STATUS}\n"
                "✓ News: {STATUS} (Count: {COUNT})\n"
                "✓ Public Announcements: {STATUS}\n\n"
                "Then provide a concise summary of ALL findings."
            ),
            context=None, # Context will be wired up in main.py
        )

    def reporting_task(self, agent, company_name):
        return Task(
            description=(
                f"Analyze the collected data for '{company_name}' and generate a professional financial risk assessment report in Turkish.\n\n"
                "# RAPOR İÇERİK GEREKSİNİMLERİ (Hedef 1000+ kelime):\n"
                "1. YÖNETİCİ ÖZETİ: Risk genel bakışı, ana bulgular ve öneriler.\n"
                "2. ŞİRKET BİLGİLERİ: Ticaret sicil detayları, sektör, adres, ihale geçmişi (varsa).\n"
                "   - Sicil veya İhale verisi 'bulunamadı' ise, bunu bir risk olarak değil, bir durum tespiti olarak not edin.\n"
                "3. YASAKLILIK LİSTESİ ANALİZİ (KRİTİK):\n"
                "   - 'Bulundu' durumu varsa => 'ŞİRKET YASAKLI LİSTEDE MEVCUT' diyerek tüm detayları (tarih, kurum) belirtin.\n"
                "   - Yoksa => 'Yasaklı listede kaydı yoktur' ifadesini kullanın ve KONTROL EDİLEN tarih aralığını belirtin.\n"
                "4. KAMU İLANLARI:\n"
                "   - SADECE bulunan ilanları özetleyin.\n"
                "   - Eğer Konkordato ilanı VARSA, bunu mutlaka vurgulayın ve risk olarak belirtin.\n"
                "   - Eğer Konkordato ilanı YOKSA, 'Konkordato ilanı bulunmamıştır' gibi cümleler KURMAYIN. Bu konuya hiç değinmeyin.\n"
                "5. HABER ANALİZİ: Haberleri, duygu durumunu ve önemli olayları özetleyin. Tüm kaynaklara atıf yapın ama Linkleri sadece Kaynaklar kısmına koyun.\n"
                "6. RİSK DEĞERLENDİRMESİ: Finansal, Yasal, İtibar ve Operasyonel riskler.\n"
                "7. SONUÇ: Nihai karar ve öneriler.\n\n"
                "KRİTİK KURALLAR:\n"
                "- LİNK KULLANIMI: Rapor metni içinde ASLA link (https://...) kullanmayın. Linkleri sadece JSON çıktısındaki 'sources' listesine ve raporun en sonundaki 'KAYNAKLAR' listesine ekleyin.\n"
                "- TON: Profesyonel Finansal Analist dili kullanın. Asla İngilizce kelime veya teknik jargon (found:false vb.) kullanmayın.\n"
                "- TARİH FORMATI: '29 Kasım 2025' gibi uzun format kullanın.\n"
                "- DOĞRULAMA: Haber/İlan verisi eksikse bunu not edin.\n\n"
                "CONFIDENCE SCORE RULES:\n"
                "- PRIORITY RULE: If multiple conditions apply, ALWAYS choose the LOWEST score range (Worst Case Scenario).\n"
                "- 15-25: BANNED (is_banned=True) OR Critical Legal Issues (Banned overrides all).\n"
                "- 20-35: KONKORDATO/Bankruptcy announcements (even if not banned).\n"
                "- 35-50: Clean but Negative News.\n"
                "- 55-70: Mixed News.\n"
                "- 70-85: Mostly Positive.\n"
                "- 85-92: Strong Positive.\n"
            ),
            agent=agent,
            output_pydantic=RiskReport,
            expected_output="A RiskReport object with detailed Turkish report_text and valid metadata."
        )
