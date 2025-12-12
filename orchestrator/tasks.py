from crewai import Task
from .schemas import RiskReport


class OrchestratorTasks:
    def research_task(self, agent, company_name, start_date, end_date):
        return Task(
            description=(
                f"Collect all available information for company '{company_name}' between '{start_date}' and '{end_date}'.\n"
                "⚠️ CRITICAL: You MUST call ALL 3 tools below. Skipping any REQUIRED tool will cause task failure.\n\n"
                "🔴 TOOL 1: Check Banned Status [REQUIRED - NEVER SKIP]\n"
                "   - YOU MUST CALL THIS TOOL FIRST!\n"
                "   - STRICT INPUT FORMAT:\n"
                "     {\"company_name\": \"" + company_name + "\", \"start_date\": \"" + start_date + "\", \"end_date\": \"" + end_date + "\", \"force_scan\": false}\n"
                "   - NEVER send tool argument schemas (type/description). Only literal primitive values (string/int/bool).\n"
                "   - NEVER change company_name/start_date/end_date values; use EXACTLY as shown above.\n"
                "   - If result is empty, do not re-check.\n\n"
                "🟡 TOOL 2: Fetch Trade Registry [OPTIONAL - if fails, continue]\n"
                "   - Example: {\"company_name\": \"" + company_name + "\", \"start_date\": \"" + start_date + "\", \"end_date\": \"" + end_date + "\"}\n"
                "   - If this tool returns 'Login Failed' or 'error', note the failure and move on immediately. Do NOT retry.\n\n"
                "🔴 TOOL 3: Fetch News [REQUIRED - NEVER SKIP]\n"
                "   ⚠️ YOU ABSOLUTELY MUST CALL THIS TOOL! THIS IS NOT OPTIONAL!\n"
                "   - STRICT INPUT FORMAT:\n"
                "     {\"company_name\": \"" + company_name + "\", \"start_date\": \"" + start_date + "\", \"end_date\": \"" + end_date + "\", \"limit\": 100}\n"
                "   - Dates must be YYYYMMDD (8 digits) - use EXACTLY: start_date=\"" + start_date + "\", end_date=\"" + end_date + "\"\n"
                "   - NEVER change the provided dates; do not invent other dates.\n"
                "   - Even if banned list or registry is empty, YOU MUST STILL FETCH NEWS!\n"
                "   - If you skip this tool, the entire task will be marked as FAILED.\n\n"
                "EXECUTION ORDER:\n"
                "   1️⃣ Call 'Check Banned Status' tool\n"
                "   2️⃣ Call 'Fetch Trade Registry' tool (if fails, continue)\n"
                "   3️⃣ Call 'Fetch News' tool (MANDATORY - do not skip under any circumstances)\n"
                "   4️⃣ Compile all raw findings into a structured summary\n\n"
                "Global guardrails:\n"
                "   - Do NOT echo or send schema metadata (type/description) to tools.\n"
                "   - Do NOT wrap values in nested objects; pass raw literals only.\n"
                "   - If a tool returns a validation error about schemas/types, immediately retry ONCE with the exact example format above; then move on.\n"
                "   - If 'Fetch Trade Registry' fails, that's OK - continue with remaining sources.\n"
                "   - Final Answer is NOT a tool; only use the provided tools.\n"
                "Compile all raw findings into a structured summary for the analyst. YOU MUST mention which tools were called and their results."
            ),
            agent=agent,
            expected_output=(
                "A comprehensive and detailed summary of raw data from all three sources. MUST include:\n"
                "- Complete findings from Banned List check with all details\n"
                "- All available Trade Registry information (or note if unavailable)\n"
                "- Detailed news analysis with FULL DETAILS:\n"
                "  * Each news title (in Turkish)\n"
                "  * Publication date\n"
                "  * Full URL/link for each news article\n"
                "  * Source name\n"
                "  * Brief summary of content\n"
                "- Any patterns, trends, or notable findings\n"
                "⚠️ CRITICAL: Pass ALL news article URLs to the analyst for inclusion in the sources field."
            )
        )

    def reporting_task(self, agent, company_name):
        return Task(
            description=(
                f"Analyze the raw data collected for '{company_name}'. "
                "Write a comprehensive, detailed, and professional financial risk assessment report.\n\n"
                "📋 RAPOR İÇERİĞİ GEREKLİLİKLERİ (Minimum 1000 kelime hedefle):\n\n"
                "1. YÖNETİCİ ÖZETİ (2-3 paragraf):\n"
                "   - Genel risk değerlendirmesi\n"
                "   - Ana bulgular ve öneriler\n"
                "   - Kritik risk faktörleri varsa vurgula\n\n"
                "2. ŞİRKET HAKKINDA GENEL BİLGİLER:\n"
                "   - Ticaret sicili bilgileri (mevcutsa)\n"
                "   - Faaliyet alanı ve sektör\n"
                "   - Tespit edilen diğer bilgiler\n\n"
                "3. YASAKLI LİSTE ANALİZİ:\n"
                "   - Resmi Gazete taraması sonuçları\n"
                "   - Herhangi bir yasak varsa detayları (tarih, neden, süre)\n"
                "   - Yasak yoksa açıkça belirt\n\n"
                "4. HABER ANALİZİ VE MEDYA İZLEMESİ:\n"
                "   - Toplanan haber sayısı ve tarih aralığı\n"
                "   - Önemli haber başlıkları ve içerikleri\n"
                "   - Pozitif/negatif haber dengesi\n"
                "   - Tespit edilen trendler ve paternler\n"
                "   - Medyada yer alan konular (finansal, hukuki, operasyonel vb.)\n\n"
                "5. RİSK DEĞERLENDİRMESİ:\n"
                "   - Finansal riskler\n"
                "   - Yasal riskler\n"
                "   - İtibar riskleri\n"
                "   - Operasyonel riskler\n"
                "   - Her risk kategorisi için detaylı açıklama\n\n"
                "6. SONUÇ VE ÖNERİLER:\n"
                "   - Genel değerlendirme\n"
                "   - Yatırım/işbirliği önerileri\n"
                "   - İzlenmesi gereken konular\n\n"
                "You must explicitly set 'is_banned' to True if the company was found in the Banned List, otherwise False.\n"
                "If 'is_banned' is True, highlight it as a CRITICAL RISK in the report text.\n"
                "Ensure the 'report_text' is in professional Turkish with detailed analysis.\n\n"
                "⚠️ YAZIM KURALLARI:\n"
                "- ASLA teknik değişken isimleri kullanma (örn: 'found: False', 'count: 0', 'status: SUCCESS')\n"
                "- Bulgulari doğal Türkçe ile ifade et: 'şirket yasaklı listede yer almamaktadır' yerine 'yasak kaydına rastlanmamıştır'\n"
                "- Tüm haber başlıkları ve içerikleri Türkçe olarak yaz (İngilizce başlık kullanma)\n"
                "- Haber kaynaklarında URL linklerini belirt\n"
                "- Tarih formatı: 8 Aralık 2025 (08 Aralık değil)\n\n"
                "⚠️ MANDATORY DATA VALIDATION:\n"
                "   - You MUST have received NEWS data from the research agent.\n"
                "   - If news data is missing, the report is INCOMPLETE and you must indicate this in status.\n"
                "   - The 'sources' field MUST include 'news' if news data was successfully retrieved.\n\n"
                "NOTE: If Trade Registry (TOBB) data failed to load, write the report based on available sources (Banned List + News). "
                "Mention in report_text that Trade Registry data was unavailable but do NOT treat it as a risk factor.\n\n"
                "⚠️ CRITICAL OUTPUT FORMAT (ZERO TOLERANCE - ANY DEVIATION CAUSES SYSTEM FAILURE):\n\n"
                "YOU MUST RETURN PURE RAW JSON WITH NO FORMATTING WHATSOEVER.\n"
                "DO NOT USE BACKTICKS (```). DO NOT USE CODE FENCES. DO NOT ADD ANY TEXT BEFORE OR AFTER.\n"
                "START YOUR RESPONSE IMMEDIATELY WITH { AND END WITH }. NOTHING ELSE.\n\n"
                "CORRECT FORMAT (START WITH { IMMEDIATELY):\n"
                '{"report_text": "Analiz metni Türkçe", "is_banned": false, "confidence_score": 75, "sources": ["news"], "status": "SUCCESS"}\n\n'
                "ABSOLUTELY FORBIDDEN (SYSTEM WILL CRASH):\n"
                "❌ ```json <- NEVER USE THIS\n"
                "❌ ``` <- NEVER USE THIS\n"
                "❌ Any text before {\n"
                "❌ Any text after }\n"
                "❌ Markdown in report_text (##, ###, *, -)\n"
                "❌ Extra keys beyond 5 required\n\n"
                "REMEMBER: Your FIRST character must be { and LAST character must be }. Period.\n\n"
                "REQUIRED FIELDS (exactly 5):\n"
                '1. "report_text": string (Turkish, plain text, no markdown)\n'
                '2. "is_banned": boolean (true/false)\n'
                '3. "confidence_score": integer (15-92, KURALLARA UYGUN)\n'
                '4. "sources": array of strings - TÜM haber linklerini içermeli ["gazette", "https://..."]\n'
                '5. "status": string ("SUCCESS" or "ERROR")\n\n'
                "⚠️ GÜVEN SKORU KURALLARI (SIKI TAKİP ET):\n"
                "- Yasaklı listede ise: confidence_score = 15-25 (çok düşük güven)\n"
                "- Yasaklı değil + negatif haberler varsa: 35-50\n"
                "- Yasaklı değil + karışık (pozitif/negatif) haberler: 55-70\n"
                "- Yasaklı değil + çoğunlukla pozitif haberler: 70-85\n"
                "- Yasaklı değil + tamamen pozitif haberler + güçlü performans: 85-92\n"
                "- Hiçbir zaman 95+ kullanma (belirsizlikler her zaman vardır)\n\n"
                "EXAMPLE CORRECT OUTPUT (copy this format exactly, no backticks):\n"
                '{"report_text": "Şirket analizi: Düşük risk profili görülmektedir.", "is_banned": false, "confidence_score": 80, "sources": ["news", "gazette"], "status": "SUCCESS"}\n\n'
                "REMEMBER: Return raw JSON only. Any backticks or markdown will cause system failure."
            ),
            agent=agent,
            output_pydantic=RiskReport,
            expected_output=(
                "A comprehensive RiskReport object with:\n"
                "- report_text: Detailed Turkish risk analysis (minimum 1000 words)\n"
                "- Covering all sections: Executive Summary, Company Info, Banned List, News Analysis, Risk Assessment, Conclusions\n"
                "- Professional tone with specific examples and data points\n"
                "- All required fields properly set"
            )
        )
