from crewai import Crew

from .agents import EmailFilterAgents
from .tasks import EmailFilterTasks

class EmailFilterCrew():
	def __init__(self):
		agents = EmailFilterAgents()
		self.filter_agent = agents.email_filter_agent()
		self.action_agent = agents.email_action_agent()
		self.writer_agent = agents.email_response_writer()

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
			verbose=True
		)
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