from typing import TypedDict, Optional, List, Dict, Any

class EmailsState(TypedDict, total=False):
    checked_emails_ids: List[str]
    emails: List[Dict]
    action_required_emails: Dict
    iteration_count: int