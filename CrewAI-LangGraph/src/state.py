from typing import TypedDict, Optional, List, Dict, Any

class EmailsState(TypedDict, total=False):
    checked_emails_ids: List[str]
    processed_thread_ids: List[str]
    emails: List[Dict]
    action_required_emails: Dict
    integration_results: Dict  # Added field to track integration results
    iteration_count: int