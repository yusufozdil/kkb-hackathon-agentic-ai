import argparse
import sys
import json
from crewai import Crew, Process
from orchestrator.agents import OrchestratorAgents
from orchestrator.tasks import OrchestratorTasks

def run_orchestrator(company_name, date_str):
    print(f"Starting AI Orchestrator for: {company_name} on {date_str}")
    
    # Initialize
    agents = OrchestratorAgents()
    tasks = OrchestratorTasks()

    # Create Agents
    researcher = agents.lead_researcher()
    analyst = agents.reporting_analyst()

    # Create Tasks
    task_research = tasks.research_task(researcher, company_name, date_str)
    task_reporting = tasks.reporting_task(analyst, company_name)

    # Define Crew
    crew = Crew(
        agents=[researcher, analyst],
        tasks=[task_research, task_reporting],
        process=Process.sequential, # Sequential execution as per PRD
        verbose=True
    )

    result = crew.kickoff()
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='AI Orchestrator for Due Diligence')
    parser.add_argument('--company', type=str, required=True, help='Company Name')
    parser.add_argument('--date', type=str, required=True, help='Date YYYYMMDD')
    
    args = parser.parse_args()
    
    try:
        final_output = run_orchestrator(args.company, args.date)
        print("\n\n######################## FINAL REPORT ########################\n")
        print(final_output)
        
        # Validation Check (Basic)
        try:
            json_out = json.loads(final_output)
            print("Valid JSON Output")
        except:
            print("Output is not pure JSON (LLM might have added text).")
            
    except Exception as e:
        print(f"Execution Failed: {e}")
        sys.exit(1)
