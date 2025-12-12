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
            goal="Collect comprehensive, detailed data about the target company from ALL available sources: Trade Registry, Banned Lists, and News.",
            backstory=(
                "You are a meticulous senior due diligence researcher with 15 years of experience. "
                "You trust only verified data and believe in exhaustive research. "
                "Your job is to use EVERY tool available and extract MAXIMUM information about a company. "
                "You systematically check all sources, note every detail, and provide thorough documentation. "
                "You never rush your work and always ensure completeness. "
                "You do not make assumptions; you only report what your tools find with full context and details."
            ),
            tools=[
                OrchestratorTools.check_banned_tool,
                OrchestratorTools.fetch_trade_registry_tool,
                OrchestratorTools.fetch_news_tool,
            ],
            allow_delegation=False,
            verbose=True,
            max_iter=20,  # Daha fazla araştırma ve veri toplama için artırıldı
            llm=llm,
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
