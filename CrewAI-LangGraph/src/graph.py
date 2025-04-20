from dotenv import load_dotenv
load_dotenv()

from langgraph.graph import StateGraph

from .state import EmailsState
from .nodes import Nodes
from .crew.crew import EmailFilterCrew

class WorkFlow():
    def __init__(self):
        nodes = Nodes()
        workflow = StateGraph(EmailsState)

        workflow.add_node("check_new_emails", nodes.check_email)
        workflow.add_node("process_emails", EmailFilterCrew().kickoff)
        workflow.add_node("integrate_emails", nodes.integrate_with_external_api)  # Add new integration node
        workflow.add_node("mark_processed", nodes.mark_threads_as_processed)
        workflow.add_node("wait_next_run", nodes.wait_next_run)

        workflow.set_entry_point("check_new_emails")
        workflow.add_conditional_edges(
                "check_new_emails",
                nodes.new_emails,
                {
                    "continue": 'process_emails',
                    "end": 'wait_next_run'
                }
        )
        workflow.add_edge('process_emails', 'integrate_emails')  # Add edge to new integration node
        workflow.add_edge('integrate_emails', 'mark_processed')  # Connect integration to mark_processed
        workflow.add_edge('mark_processed', 'wait_next_run')
        workflow.add_edge('wait_next_run', 'check_new_emails')
        self.app = workflow.compile()