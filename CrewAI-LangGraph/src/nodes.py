import os
import time
import requests
from dotenv import load_dotenv
from src.msgraph_client import MSGraphClient

# Load environment variables
load_dotenv()

# Sender filter configuration from .env (trimmed + safe)
ALLOWED_SENDERS = [s.strip() for s in os.getenv("ALLOWED_SENDERS", "").split(",") if s.strip()]
ALLOWED_DOMAINS = [s.strip() for s in os.getenv("ALLOWED_DOMAINS", "").split(",") if s.strip()]
BLOCKED_KEYWORDS = [s.strip() for s in os.getenv("BLOCKED_KEYWORDS", "").split(",") if s.strip()]

class Nodes():
    def __init__(self):
        self.msgraph = MSGraphClient(
            client_id=os.environ['MS_CLIENT_ID'],
            client_secret=os.environ['MS_CLIENT_SECRET'],
            tenant_id=os.environ['MS_TENANT_ID'],
            user_email=os.environ['MS_USER_EMAIL']
        )

    def is_valid_sender(self, sender: str, my_email: str) -> bool:
        if not sender or my_email in sender:
            return False

        # No filters = allow all (except self)
        allow_all = not ALLOWED_SENDERS and not ALLOWED_DOMAINS and not BLOCKED_KEYWORDS

        if allow_all:
            return True

        if sender in ALLOWED_SENDERS:
            return True

        if any(sender.endswith(f"@{domain}") for domain in ALLOWED_DOMAINS):
            if not any(keyword in sender for keyword in BLOCKED_KEYWORDS):
                return True

        return False

    def check_email(self, state):
        print("# Checking for new emails (MS Graph)")
        if not self.msgraph.get_token():
            return state

        headers = {"Authorization": f"Bearer {self.msgraph.access_token}"}
        response = requests.get(
            f"https://graph.microsoft.com/v1.0/users/{self.msgraph.user_email}/messages?$top=10&$orderby=receivedDateTime desc",
            headers=headers
        )

        emails = response.json().get('value', [])
        new_emails = []
        thread_ids = []
        checked_emails = state.get('checked_emails_ids') or []
        my_email = os.environ.get('MY_EMAIL', '')

        for email in emails:
            sender = (
                email.get('from', {})
                .get('emailAddress', {})
                .get('address', '')
            )

            print(f"🕵️ Checking sender: {sender}")
            if not self.is_valid_sender(sender, my_email):
                print(f"❌ Skipped: {sender}")
                continue

            if email.get('id') and email['id'] not in checked_emails:
                thread_id = email.get('conversationId')
                if thread_id and thread_id not in thread_ids:
                    new_emails.append({
                        'id': email['id'],
                        'threadId': thread_id,
                        'snippet': email.get('bodyPreview', ''),
                        'sender': sender
                    })
                    thread_ids.append(thread_id)
                    print(f"✅ New Email Added: {sender}")

        checked_emails.extend([email.get('id') for email in emails if email.get('id')])
        return {**state, 'emails': new_emails, 'checked_emails_ids': checked_emails}

    def wait_next_run(self, state):
        print("## Waiting for 20 seconds")
        time.sleep(20)
        return state

    def new_emails(self, state):
        return "continue" if state.get('emails') else "end"
