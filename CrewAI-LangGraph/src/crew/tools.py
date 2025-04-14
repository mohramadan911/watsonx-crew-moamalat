from langchain.tools import tool
from src.msgraph_client import MSGraphClient
import os
import requests

class CreateDraftTool():
    @tool("Create Draft")
    def create_draft(data):
        """
        Create an email draft using Microsoft Graph.
        Input format: to|subject|message or JSON object
        """
        try:
            # Try JSON format first
            if isinstance(data, dict):
                to = data.get("to")
                subject = data.get("subject")
                message = data.get("message")
            elif data.startswith("{") and data.endswith("}"):
                # JSON as string
                import json
                parsed = json.loads(data)
                to = parsed.get("to")
                subject = parsed.get("subject")
                message = parsed.get("message")
            else:
                # Fall back to pipe-delimited
                to, subject, message = data.split('|')
                
            client = MSGraphClient(
                client_id=os.environ['MS_CLIENT_ID'],
                client_secret=os.environ['MS_CLIENT_SECRET'],
                tenant_id=os.environ['MS_TENANT_ID'],
                user_email=os.environ['MS_USER_EMAIL']
            )
            print(f"Creating draft to: {to}, subject: {subject}")
            success = client.send_email(to_email=to, subject=subject, body=message)
            return f"Draft {'created' if success else 'failed'}"
        except Exception as e:
            print(f"Error creating draft: {str(e)}")
            return f"Draft failed: {str(e)}"

class EmailThreadTool():
    @tool("Fetch Email Thread")
    def fetch_thread(thread_id: str):
        """
        Fetch full email thread from Microsoft Graph using a thread ID.
        Input: a thread/conversation ID string
        Output: full thread content (concatenated emails)
        """
        client = MSGraphClient(
            client_id=os.environ['MS_CLIENT_ID'],
            client_secret=os.environ['MS_CLIENT_SECRET'],
            tenant_id=os.environ['MS_TENANT_ID'],
            user_email=os.environ['MS_USER_EMAIL']
        )
        if not client.get_token():
            return "Unable to retrieve token"

        headers = {"Authorization": f"Bearer {client.access_token}"}
        
        # Method 1: Try to fetch messages directly (without filtering by conversationId)
        url = f"https://graph.microsoft.com/v1.0/users/{client.user_email}/messages?$top=10&$orderby=receivedDateTime desc"
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            return f"Error fetching messages: {response.text}"
        
        # Filter the messages by conversationId on the client side
        all_messages = response.json().get('value', [])
        thread_messages = [msg for msg in all_messages if msg.get('conversationId') == thread_id]
        
        if not thread_messages:
            # Alternative method: Try to get the specific message if we have its ID
            # This works if thread_id might actually be a message ID
            url = f"https://graph.microsoft.com/v1.0/users/{client.user_email}/messages/{thread_id}"
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                message = response.json()
                thread_messages = [message]
        
        full_thread = "\n\n".join(
            f"From: {email['from']['emailAddress']['address']}\nSubject: {email.get('subject')}\n\n{email.get('body', {}).get('content', '')}"
            for email in thread_messages
        )
        
        return full_thread or "No emails found in thread"
