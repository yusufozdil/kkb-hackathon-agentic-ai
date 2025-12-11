from crewai import Agent
from .tools import OrchestratorTools

llm = "ollama/gemma3:4b"


class OrchestratorAgents:
    def lead_researcher(self):
        return Agent(
            role="Lead Researcher",
            goal="Collect comprehensive data about the target company from Trade Registry, Banned Lists, and News.",
            backstory=(
                "You are an obsessive auditor who trusts only verified data. "
                "Your job is to use every tool available to dig up information about a company. "
                "You do not make assumptions; you only report what your tools find."
            ),
            tools=[
                OrchestratorTools.check_banned_tool,
                OrchestratorTools.fetch_trade_registry_tool,
                OrchestratorTools.fetch_news_tool,
            ],
            allow_delegation=False,
            verbose=True,
            max_iter=10,  # Stop infinite loops
            llm=llm,
        )

    def reporting_analyst(self):
        return Agent(
            role="Reporting Analyst",
            goal="Synthesize collected data into a professional financial risk report in Turkish.",
            backstory=(
                "You are a senior financial risk analyst. You write clear, concise, and reliable reports for top management. "
                "You ONLY write in TURKISH. You do not hallucinate."
            ),
            tools=[],  # Analyst mostly just reads the context provided by Researcher
            allow_delegation=False,
            verbose=True,
            max_iter=10,
            llm=llm,
        )
