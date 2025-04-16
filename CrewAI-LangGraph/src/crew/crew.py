# crew.py
from crewai import Crew
from .agents import EmailFilterAgents
from .tasks import EmailFilterTasks
import os
import logging

# Import using current approach
from langchain.callbacks.tracers import LangChainTracer
import langsmith

class EmailFilterCrew():
    def __init__(self):
        agents = EmailFilterAgents()
        self.filter_agent = agents.email_filter_agent()
        self.action_agent = agents.email_action_agent()
        self.writer_agent = agents.email_response_writer()
        
        # Set up callbacks list
        self.callbacks = []
        
        # Set up tracing
        try:
            # Initialize tracing - cleaner approach for langchain-v2
            project_name = os.getenv("LANGSMITH_PROJECT", "email-automation")
            
            # Check if LangSmith is configured
            if os.getenv("LANGSMITH_API_KEY"):
                # Register a callback for tracing
                tracer = langsmith.Client().as_callback(project_name=project_name)
                self.callbacks.append(tracer)
                print(f"LangSmith tracing initialized for project: {project_name}")
        except Exception as e:
            logging.warning(f"Failed to initialize LangSmith tracing: {str(e)}")

    def kickoff(self, state):
        # Safely handle None values
        current_count = state.get("iteration_count")
        if current_count is None:
            current_count = 0
        
        # Increment counter
        state["iteration_count"] = current_count + 1
        
        # Add a safety check
        if state.get("iteration_count", 0) > 10:  # Adjust as needed
            print("Maximum iterations reached, terminating workflow")
            return {**state, "action_required_emails": "Max iterations reached"}
        
        print("### Filtering emails")
        tasks = EmailFilterTasks()
        
        crew = Crew(
            agents=[self.filter_agent, self.action_agent, self.writer_agent],
            tasks=[
                tasks.filter_emails_task(self.filter_agent, self._format_emails(state['emails'])),
                tasks.action_required_emails_task(self.action_agent),
                tasks.draft_responses_task(self.writer_agent)
            ],
            verbose=True,
            callbacks=self.callbacks
        )
        
        # Run the crew
        result = crew.kickoff()
        
        return {**state, "action_required_emails": result}

    def _format_emails(self, emails):
        emails_string = []
        for email in emails:
            print(f"Email ID: {email['id']}")
            print(f"Snippet length: {len(email.get('snippet', ''))}")
            
            # Strictly limit snippet size
            snippet = email.get('snippet', '')
            if len(snippet) > 200:
                snippet = snippet[:200] + "..."
            
            arr = [
                f"ID: {email['id']}",
                f"- Thread ID: {email['threadId']}",
                f"- Snippet: {snippet}",
                f"- From: {email['sender']}",
                f"--------"
            ]
            emails_string.append("\n".join(arr))
        return "\n".join(emails_string)