from crewai import Task
from .schemas import RiskReport

class OrchestratorTasks:
    def research_task(self, agent, company_name, date_str):
        return Task(
            description=(
                f"Collect all available information for company '{company_name}' for the date '{date_str}'.\n"
                "1. Check if the company is in the Banned List (Official Gazette).\n"
                "   - USE 'company_name' argument in the tool for faster search.\n"
                "   - IMPORTANT: If the list is empty [], it means the company is NOT banned. Do NOT check again.\n"
                "2. Fetch Trade Registry details (Capital, Managers, Address).\n"
                "3. Fetch News and Sentiment analysis.\n"
                "Compile all raw findings into a structured summary for the analyst. Stop searching once you have checked all 3 sources."
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
                "Ensure the 'report_text' is in professional Turkish.\n"
                "IMPORTANT: Do NOT include the confidence score or list of sources in the 'report_text' field. These belong in their own separate fields."
            ),
            agent=agent,
            output_pydantic=RiskReport,
            expected_output="A structured RiskReport object."
        )
