import argparse
import sys
import json
import os
from datetime import datetime
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
        
        # Convert Pydantic model to JSON
        if hasattr(final_output, 'model_dump_json'):
            # Pydantic v2
            json_output = final_output.model_dump_json(indent=2)
        elif hasattr(final_output, 'json'):
            # Pydantic v1
            json_output = final_output.json(indent=2)
        else:
            # Fallback to string representation
            json_output = str(final_output)
        
        # Print to console
        print(json_output)
        print("\n✅ Valid JSON Output")
        
        # Save to file
        os.makedirs("reports", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reports/{args.company}_{args.start}_{args.end}_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(json_output)
        
        print(f"📄 Rapor kaydedildi: {filename}")

    except Exception as e:
        print(f"❌ Execution Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
