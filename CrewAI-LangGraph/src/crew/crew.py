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
        self.logger = logging.getLogger(__name__)  # ✅ Add this line

        agents = EmailFilterAgents()
        self.filter_agent = agents.email_filter_agent()
        self.action_agent = agents.email_action_agent()
        
        # Set up callbacks list
        self.callbacks = []
        
        # Set up tracing
        try:
            project_name = os.getenv("LANGSMITH_PROJECT", "email-automation")
            if os.getenv("LANGSMITH_API_KEY"):
                tracer = langsmith.Client().as_callback(project_name=project_name)
                self.callbacks.append(tracer)
                print(f"LangSmith tracing initialized for project: {project_name}")
        except Exception as e:
            logging.warning(f"Failed to initialize LangSmith tracing: {str(e)}")


    def kickoff(self, state):
        # Safely handle None values
        current_count = state.get("iteration_count", 0)
        state["iteration_count"] = current_count + 1
        
        if state["iteration_count"] > 10:
            print("Maximum iterations reached, terminating workflow")
            return {**state, "action_required_emails": "Max iterations reached"}
        
        print("### Filtering emails")
        tasks = EmailFilterTasks()
        
        crew = Crew(
            agents=[self.filter_agent, self.action_agent],
            tasks=[
                tasks.filter_emails_task(self.filter_agent, self._format_emails(state['emails'])),
                tasks.action_required_emails_task(self.action_agent)
            ],
            verbose=True,
            callbacks=self.callbacks
        )
        
        # Run the crew
        result = crew.kickoff()
        self.logger.info(f"Crew result: {result}")

        # Extract final_output to pass as plain text
        if hasattr(result, "final_output"):
            output_text = result.final_output
            print("✔️ Extracted final_output from Crew result.")
        else:
            output_text = str(result)
            print("⚠️ Crew result did not have final_output. Falling back to string representation.")
        
        return {**state, "action_required_emails": output_text}

    def _format_emails(self, emails):
        emails_string = []
        for email in emails:
            print(f"Email ID: {email['id']}")
            print(f"Snippet length: {len(email.get('snippet', ''))}")
            
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
