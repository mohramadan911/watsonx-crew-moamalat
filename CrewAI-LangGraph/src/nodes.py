import os
import time
import requests
from dotenv import load_dotenv
from src.msgraph_client import MSGraphClient
from src.integration import integrate_emails  # Import the new integration function

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
        try:
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
            
            # Initialize tracking lists if they don't exist
            checked_emails = state.get('checked_emails_ids') or []
            processed_thread_ids = state.get('processed_thread_ids') or []
            
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

                # Get both ID and thread ID
                email_id = email.get('id')
                thread_id = email.get('conversationId')
                
                # Only process if:
                # 1. We haven't seen this email ID before
                # 2. We haven't processed this thread ID before
                if email_id and email_id not in checked_emails and thread_id and thread_id not in processed_thread_ids:
                    if thread_id not in thread_ids:  # Avoid duplicates in current batch
                        # Limit snippet size to reduce token usage
                        snippet = email.get('bodyPreview', '')
                        if len(snippet) > 300:
                            snippet = snippet[:300] + "..."
                            
                        new_emails.append({
                            'id': email_id,
                            'threadId': thread_id,
                            'snippet': snippet,
                            'sender': sender,
                            'subject': email.get('subject', 'No Subject')  # Add subject for integration
                        })
                        thread_ids.append(thread_id)
                        print(f"✅ New Email Added: {sender}")

            # Mark all emails as checked
            checked_emails.extend([email.get('id') for email in emails if email.get('id')])
            
            # Update state with new emails and tracking information
            return {
                **state, 
                'emails': new_emails, 
                'checked_emails_ids': checked_emails
            }
        except Exception as e:
            print(f"Error checking emails: {str(e)}")
            return {**state, 'emails': [], 'error': str(e)}

    def wait_next_run(self, state):
        print("## Waiting for 20 seconds")
        time.sleep(20)
        return state

    def new_emails(self, state):
        return "continue" if state.get('emails') else "end"
    
    def integrate_with_external_api(self, state):
        """Integrate processed emails with the external API system"""
        print("## Integrating emails with external API")
        
        # Check if we have any action required emails to integrate
        action_required_emails = state.get('action_required_emails')
        if not action_required_emails:
            print("No action required emails to integrate")
            return {**state, 'integration_results': {"success": False, "message": "No emails to integrate"}}
        
        try:
            # Call the integration function
            integration_results = integrate_emails(action_required_emails)
            
            # Log the results
            success_count = sum(1 for r in integration_results.get('results', []) if r.get('integration_result', {}).get('success', False))
            total_count = len(integration_results.get('results', []))
            
            print(f"## Integration complete: {success_count}/{total_count} emails successfully integrated")
            
            # Return updated state with integration results
            return {**state, 'integration_results': integration_results}
            
        except Exception as e:
            print(f"Error integrating emails: {str(e)}")
            return {**state, 'integration_results': {"success": False, "message": f"Integration error: {str(e)}"}}
    
    def mark_threads_as_processed(self, state):
        """Mark all processed email threads as processed to avoid duplicate responses"""
        processed_thread_ids = state.get('processed_thread_ids') or []
        
        # Add all thread IDs from current batch to processed list
        for email in state.get('emails', []):
            thread_id = email.get('threadId')
            if thread_id and thread_id not in processed_thread_ids:
                processed_thread_ids.append(thread_id)
                print(f"📝 Marked thread {thread_id} as processed")
        
        # Update state with processed thread IDs
        return {**state, 'processed_thread_ids': processed_thread_ids}