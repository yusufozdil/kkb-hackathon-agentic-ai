import argparse
import sys
import json
from crewai import Crew, Process
from orchestrator.agents import OrchestratorAgents
from orchestrator.tasks import OrchestratorTasks


def run_orchestrator(company_name, start_date, end_date):
    print(f"Starting AI Orchestrator for: {company_name} | {start_date} - {end_date}")

    agents = OrchestratorAgents()
    tasks = OrchestratorTasks()

    researcher = agents.lead_researcher()
    analyst = agents.reporting_analyst()

    task_research = tasks.research_task(researcher, company_name, start_date, end_date)
    task_reporting = tasks.reporting_task(analyst, company_name)

    crew = Crew(
        agents=[researcher, analyst],
        tasks=[task_research, task_reporting],
        process=Process.sequential,
        verbose=True
    )

    result = crew.kickoff()
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Orchestrator for Due Diligence")
    parser.add_argument("--company", type=str, required=True, help="Company Name")
    parser.add_argument("--start", type=str, required=True, help="Start date YYYYMMDD")
    parser.add_argument("--end", type=str, required=True, help="End date YYYYMMDD")

    args = parser.parse_args()

    try:
        final_output = run_orchestrator(args.company, args.start, args.end)
        print("\n\n######################## FINAL REPORT ########################\n")
        print(final_output)

        try:
            json.loads(final_output)
            print("Valid JSON Output")
        except Exception:
            print("Output is not pure JSON (LLM might have added text).")

    except Exception as e:
        print(f"Execution Failed: {e}")
        sys.exit(1)
