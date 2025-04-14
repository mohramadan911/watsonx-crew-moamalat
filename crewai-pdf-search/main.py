#!/usr/bin/env python3
"""
Main entry point for the CrewAI PDF Search application.

This script sets up and executes a CrewAI crew to analyze PDF documents
using semantic search capabilities.
"""
import os
from crewai import Crew, Process
from dotenv import load_dotenv
from config.settings import VERBOSE, OLLAMA_MODEL, OLLAMA_API_BASE

# Load environment variables from .env file
load_dotenv()

# Import project modules
from agents import agent_1, agent_2, agent_3
from tasks import create_tasks
from utils.download_pdf import download_sample_pdf
from config.settings import VERBOSE


def main():
    """
    Main function to run the CrewAI PDF Search application.
    """
    print("## Welcome to the CrewAI PDF Search Tool Demo")
    print('-------------------------------------------')
    
    # Download the sample PDF if not already present
    download_sample_pdf()
    
    # Get user input for variables
    var_1 = input("ما هي الحقول التي تريد استخراجها من الوثيقة؟ (مثال: الرقم الداخلي، التاريخ، الموضوع)\n")
    var_2 = input("ما نوع الوثيقة؟ (مثال: إشعار، خطاب، تقرير رسمي)\n")
    var_3 = input("ما مستوى التفصيل المطلوب؟ (مثال: ملخص، تحليل شامل، فهم للسياق)\n")
    print("-------------------------------")
    
    # Create tasks with user variables
    from agents import agent_1, agent_2, agent_3, agent_metadata
    tasks = create_tasks(var_1, var_2, var_3, [agent_1, agent_2, agent_3, agent_metadata])
    
    # Instantiate the crew with a sequential process
    crew = Crew(
        agents=[agent_1, agent_2, agent_3],
        tasks=tasks,
        verbose=VERBOSE,
        process=Process.sequential
    )
    
    # Define inputs for task execution
    inputs = {
        "var_1": var_1,
        "var_2": var_2,
        "var_3": var_3
    }
    
    # Execute the crew
    result = crew.kickoff(inputs=inputs)
    
    # Display the results
    print("\n\n########################")
    print("## CrewAI PDF Search Tool Result:")
    print("########################\n")
    print(result)
    
    # Inform user about output files
    print("\n\nDetailed outputs from each agent have been saved to the 'output-files' directory.")
    
    return result

if __name__ == "__main__":
    main()