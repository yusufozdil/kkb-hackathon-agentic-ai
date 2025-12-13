from crewai import Agent
from crewai.llm import LLM
from .tools import OrchestratorTools
import sys
import os

# Config dosyasını import et - bu OPENAI_API_KEY ve OPENAI_BASE_URL'i ayarlar
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

# Kloudeks API için LLM objesi oluştur
# gpt-oss-120b güçlü bir model - daha uzun ve detaylı çıktılar için optimize edildi
llm = LLM(
    model="openai/gpt-oss-120b",
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
    temperature=0.7,
    max_tokens=8192  # Uzun ve detaylı raporlar için artırıldı
)


class OrchestratorAgents:
    def lead_researcher(self):
        return Agent(
            role="Lead Researcher",
            goal="I WILL call exactly 4 tools in strict sequence: 1) Check Banned Status 2) Fetch Trade Registry 3) Fetch News 4) Fetch Public Announcements. I will NOT provide Final Answer until ALL 4 tools are called.",
            backstory=(
                "You are a robotic, methodical data collector who follows instructions EXACTLY as written. "
                "You do NOT think, interpret, or make decisions - you simply execute tools in sequence. "
                "\n\n"
                "YOUR ONLY JOB:\n"
                "1️⃣ Call 'Check Banned Status' → document result → continue\n"
                "2️⃣ Call 'Fetch Trade Registry' → document result → continue\n"
                "3️⃣ Call 'Fetch News' → document result → continue\n"
                "4️⃣ Call 'Fetch Public Announcements' → document result → continue\n"
                "5️⃣ Provide Final Answer with ALL 4 tool results\n"
                "\n"
                "STRICT RULES:\n"
                "❌ You CANNOT skip step 3 (Fetch News) even if steps 1-2 have data\n"
                "❌ You CANNOT skip step 4 (Fetch Public Announcements) even if steps 1-3 have data\n"
                "❌ You CANNOT provide Final Answer before completing ALL 4 steps\n"
                "❌ You CANNOT make up or assume tool results - if you didn't call it, you don't have data\n"
                "✅ You MUST call each tool INDIVIDUALLY with separate tool invocations\n"
                "✅ You MUST wait for actual tool response before moving to next tool\n"
                "\n"
                "If you provide Final Answer after only 2 tools, your work will be REJECTED."
            ),
            tools=[
                OrchestratorTools.check_banned_tool,
                OrchestratorTools.fetch_trade_registry_tool,
                OrchestratorTools.fetch_news_tool,
                OrchestratorTools.fetch_ilan_gov_tool,  # Konkordato için KRİTİK!
                OrchestratorTools.fetch_ihale_tool,
            ],
            allow_delegation=False,
            verbose=True,
            max_iter=35,  # 4 tool + retrials
            llm=llm,
            memory=False,  # Disable memory to prevent over-thinking
            respect_context_window=True,
        )

    def reporting_analyst(self):
        return Agent(
            role="Reporting Analyst",
            goal="Synthesize collected data into a comprehensive, detailed, professional financial risk assessment report in Turkish.",
            backstory=(
                "You are a distinguished senior financial risk analyst with expertise in credit analysis and due diligence. "
                "You have 20 years of experience writing thorough risk assessment reports for C-level executives and investment committees. "
                "Your reports are known for being comprehensive, well-structured, insightful, and actionable. "
                "You always write detailed analyses covering multiple dimensions of risk (financial, legal, reputational, operational). "
                "You provide context, interpret findings, identify patterns, and give clear recommendations. "
                "You ONLY write in PROFESSIONAL TURKISH and NEVER hallucinate - every statement is backed by collected data. "
                "You believe in thorough documentation and your reports are typically 1000+ words with clear sections and detailed analysis.\n\n"
                "CRITICAL WRITING RULES YOU ALWAYS FOLLOW:\n"
                "1. NEVER use technical variable names (like 'found: False', 'count: 0', 'status: SUCCESS') - write naturally in Turkish\n"
                "2. ALL news titles and content MUST be in Turkish (never use English headlines)\n"
                "3. Include EVERY news article URL in the sources field\n"
                "4. Use proper date format: '8 Aralık 2025' not '08 Aralık 2025'\n"
                "5. Confidence scores must follow strict rules based on findings\n"
                "6. Write as a professional analyst, not as a programmer"
            ),
            tools=[],  # Analyst mostly just reads the context provided by Researcher
            allow_delegation=False,
            verbose=True,
            max_iter=15,  # Detaylı rapor yazımı için artırıldı
            llm=llm,
        )
