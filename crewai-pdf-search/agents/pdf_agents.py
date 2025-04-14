"""
Agent definitions for the PDF Search project.
"""
from textwrap import dedent
from crewai import Agent
from langchain_openai import ChatOpenAI
# Uncomment to use other LLM providers
# from langchain_groq import ChatGroq
# from langchain_anthropic import ChatAnthropic
# from langchain_community.chat_models import ChatCohere
from langchain_ollama import ChatOllama
from config.settings import OLLAMA_MODEL, OLLAMA_API_BASE

from tools import pdf_search_tool
from config.settings import DEFAULT_MODEL, DEFAULT_TEMPERATURE, MAX_RPM, MAX_ITERATIONS, VERBOSE

def create_agent(
    role,
    backstory,
    goal,
    tools=None,
    allow_delegation=False,
    llm_model=DEFAULT_MODEL,
    temperature=DEFAULT_TEMPERATURE,
    verbose=VERBOSE,
    max_iter=MAX_ITERATIONS,
    max_rpm=MAX_RPM
):
    """
    Create an agent with the specified parameters.
    
    Args:
        role (str): The agent's role.
        backstory (str): The agent's backstory.
        goal (str): The agent's goal.
        tools (list, optional): The tools available to the agent. Defaults to None.
        allow_delegation (bool, optional): Whether the agent can delegate tasks. Defaults to False.
        llm_model (str, optional): The LLM model to use. Defaults to DEFAULT_MODEL.
        temperature (float, optional): The temperature for the LLM. Defaults to DEFAULT_TEMPERATURE.
        verbose (bool, optional): Whether the agent execution should be verbose. Defaults to VERBOSE.
        max_iter (int, optional): Maximum iterations before giving best answer. Defaults to MAX_ITERATIONS.
        max_rpm (int, optional): Maximum requests per minute to the LLM. Defaults to MAX_RPM.
        
    Returns:
        Agent: An initialized Agent instance.
    """
    if tools is None:
        tools = [pdf_search_tool]
    
    # Initialize the LLM
    llm = ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_API_BASE,
        temperature=temperature
    )
    
    # Create and return the agent
    return Agent(
        role=dedent(role),
        backstory=dedent(backstory),
        goal=dedent(goal),
        tools=tools,
        allow_delegation=allow_delegation,
        verbose=verbose,
        max_iter=max_iter,
        max_rpm=max_rpm,
        llm=llm
    )

# Define specific agents
agent_1 = create_agent(
    role="""
    Research Analyst specialized in PDF document analysis.
    """,
    backstory="""
    You are a skilled research analyst with expertise in extracting relevant information
    from academic papers and technical documents. Your analytical skills allow you to
    identify key concepts, methodologies, and findings from complex PDFs.
    """,
    goal="""
    Extract and summarize the core concepts and methodologies from PDF documents,
    providing clear explanations of technical content.
    """
)

agent_2 = create_agent(
    role="""
    Technical Content Specialist with expertise in transforming complex information
    into structured knowledge.
    """,
    backstory="""
    You have years of experience working with technical content from various domains.
    Your specialty is organizing complex information into coherent structures that
    highlight relationships between concepts and ideas.
    """,
    goal="""
    Create structured knowledge representations from the analyzed PDF content,
    organizing information into logical categories and hierarchies.
    """
)

agent_3 = create_agent(
    role="""
    Final Report Generator specialized in creating comprehensive summaries and insights.
    """,
    backstory="""
    You excel at synthesizing information from multiple sources and perspectives.
    Your reports are known for their clarity, completeness, and actionable insights.
    """,
    goal="""
    Generate a comprehensive final report that combines the findings and analysis
    from previous agents, presenting a cohesive and valuable output.
    """
)

agent_metadata = create_agent(
    role="""
    Arabic Document Metadata Extractor.
    """,
    backstory="""
    You are an expert in Arabic document formats and can extract structured metadata from PDFs including document number, date, recipient, and subject.
    """,
    goal="""
    Identify and extract key metadata from Arabic documents such as internal number, date, recipient, and subject.
    Return the output in Markdown with labels and values in Arabic.
    """
)