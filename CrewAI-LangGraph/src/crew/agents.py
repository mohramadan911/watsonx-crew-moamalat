# agents.py
from crewai import Agent
from textwrap import dedent

class EmailFilterAgents():
    def email_filter_agent(self):
        return Agent(
            role='Senior Email Analyst',
            goal='Filter non-essential emails',
            backstory=dedent("""
                You analyze and filter email content, spotting important emails and ignoring newsletters.
            """),
            verbose=True,
            allow_delegation=False
        )

    def email_action_agent(self):
        return Agent(
            role='Email Action Specialist',
            goal='Identify action-required emails',
            backstory=dedent("""
                You identify emails needing a response, summarize context and urgency.
                You must analyze the email thread contents provided to you.
            """),
            # Remove tools completely to avoid format issues
            verbose=True,
            allow_delegation=False
        )