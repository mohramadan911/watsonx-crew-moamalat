# agents.py
from crewai import Agent
from textwrap import dedent
from .tools import CreateDraftTool, EmailThreadTool
from langchain_community.tools.tavily_search import TavilySearchResults
# You can add this line if your agents use LLMs directly
# from langchain_openai import ChatOpenAI

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
                You must fetch the full thread using its ID before summarizing.
            """),
            tools=[
                TavilySearchResults(),
                EmailThreadTool.fetch_thread  # ← Added thread fetcher tool
            ],
            verbose=True,
            allow_delegation=False
        )

    def email_response_writer(self):
        return Agent(
            role='Email Response Writer',
            goal='Draft appropriate responses to important emails',
            backstory=dedent("""
                You write clear and helpful responses, using the user's tone.
            """),
            tools=[
                TavilySearchResults(),
                CreateDraftTool.create_draft
            ],
            verbose=True,
            allow_delegation=False
        )