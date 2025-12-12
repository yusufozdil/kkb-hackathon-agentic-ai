from crewai import Task
from .schemas import RiskReport


class OrchestratorTasks:
    def research_task(self, agent, company_name, start_date, end_date):
        return Task(
            description=(
                f"Collect all available information for company '{company_name}' between '{start_date}' and '{end_date}'.\n"
                "PRIORITY: Gather data from ALL 3 sources below. If any source fails, continue with remaining sources.\n\n"
                "1. Check if the company is in the Banned List (Official Gazette) for this date range. [REQUIRED]\n"
                "   - STRICT INPUT FORMAT EXAMPLES (do NOT invent other schemas):\n"
                "     {\"company_name\": \"ACME\", \"start_date\": \"" + start_date + "\", \"end_date\": \"" + end_date + "\", \"force_scan\": false}\n"
                "   - NEVER send tool argument schemas (type/description). Only literal primitive values (string/int/bool). No nested dicts.\n"
                "   - NEVER change company_name/start_date/end_date values; use exactly the provided inputs.\n"
                "   - If result is empty, do not re-check.\n\n"
                "2. Fetch Trade Registry details (Capital, Managers, Address) within the same date range. [OPTIONAL - if fails, continue]\n"
                "   - Example: {\"company_name\": \"ACME\", \"start_date\": \"" + start_date + "\", \"end_date\": \"" + end_date + "\"}\n"
                "   - If this tool returns 'Login Failed' or 'error', note the failure and move on immediately. Do NOT retry.\n\n"
                "3. Fetch News and sentiment analysis within the same date range. [REQUIRED]\n"
                "   - Example: {\"company_name\": \"ACME\", \"start_date\": \"" + start_date + "\", \"end_date\": \"" + end_date + "\", \"limit\": 50}\n"
                "   - Dates must be YYYYMMDD or YYYY-MM-DD; prefer YYYYMMDD.\n"
                "   - NEVER change the provided start_date/end_date; do not invent other dates.\n\n"
                "Global guardrails:\n"
                "   - Do NOT echo or send schema metadata (type/description) to tools.\n"
                "   - Do NOT wrap values in nested objects; pass raw literals only.\n"
                "   - If a tool returns a validation error about schemas/types, immediately retry ONCE with the exact example format above; then move on.\n"
                "   - If a tool returns 'Login Failed' or 'error', accept the failure and continue with remaining sources.\n"
                "   - Final Answer is NOT a tool; only use the provided tools.\n"
                "Compile all raw findings into a structured summary for the analyst. Include both successful and failed sources."
            ),
            agent=agent,
            expected_output="A detailed summary of raw data found from all three sources."
        )

    def reporting_task(self, agent, company_name):
        return Task(
            description=(
                f"Analyze the raw data collected for '{company_name}'. "
                "Write a final risk assessment report.\n"
                "You must explicitly set 'is_banned' to True if the company was found in the Banned List, otherwise False.\n"
                "If 'is_banned' is True, highlight it as a CRITICAL RISK in the report text.\n"
                "Ensure the 'report_text' is in professional Turkish.\n\n"
                "NOTE: If Trade Registry (TOBB) data failed to load, write the report based on available sources (Banned List + News). "
                "Mention in report_text that Trade Registry data was unavailable but do NOT treat it as a risk factor.\n\n"
                "⚠️ CRITICAL OUTPUT FORMAT (ZERO TOLERANCE):\n"
                "Your response MUST BE PURE JSON - NO BACKTICKS (```), NO MARKDOWN, NO CODE FENCES, NO TEXT BEFORE/AFTER.\n"
                "Return ONLY this exact structure:\n"
                '{"report_text": "Turkish risk analysis here", "is_banned": false, "confidence_score": 75, "sources": ["news"], "status": "SUCCESS"}\n\n'
                "FORBIDDEN:\n"
                "- ``` json  <- NO BACKTICKS EVER\n"
                "- ```       <- NO BACKTICKS EVER\n"
                "- Extra keys beyond the 5 required fields\n"
                "- Markdown headings (##, ###) in report_text\n"
                "- Bullet points or lists in report_text\n"
                "- Text before or after the JSON\n\n"
                "REQUIRED FIELDS (exactly 5):\n"
                '1. "report_text": string (Turkish, plain text, no markdown)\n'
                '2. "is_banned": boolean (true/false)\n'
                '3. "confidence_score": integer (0-100)\n'
                '4. "sources": array of strings\n'
                '5. "status": string ("SUCCESS" or "ERROR")\n\n'
                "Consistency rule: If report_text implies medium/high risk, confidence_score must NOT be high (cap at 60). "
                "If report_text implies low risk, confidence_score should be 70-90.\n\n"
                "EXAMPLE CORRECT OUTPUT (copy this format exactly, no backticks):\n"
                '{"report_text": "Şirket analizi: Düşük risk profili görülmektedir.", "is_banned": false, "confidence_score": 80, "sources": ["news", "gazette"], "status": "SUCCESS"}\n\n'
                "REMEMBER: Return raw JSON only. Any backticks or markdown will cause system failure."
            ),
            agent=agent,
            output_pydantic=RiskReport,
            expected_output="A structured RiskReport object."
        )
