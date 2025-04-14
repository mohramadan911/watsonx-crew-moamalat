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
            elif isinstance(data, str) and data.startswith("{") and "}" in data:
                # JSON as string
                import json
                try:
                    parsed = json.loads(data)
                    to = parsed.get("to")
                    subject = parsed.get("subject")
                    message = parsed.get("message")
                except json.JSONDecodeError:
                    # If JSON parsing fails, try pipe-delimited format
                    to, subject, message = data.split('|')
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
        Fetch email thread summary with attachment info
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
        
        # Use $select to only get needed fields
        url = f"https://graph.microsoft.com/v1.0/users/{client.user_email}/messages?$filter=conversationId eq '{thread_id}'&$select=id,subject,from,receivedDateTime,bodyPreview,hasAttachments&$top=5&$orderby=receivedDateTime desc"
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 400:  # If filter is still too complex
                # Fallback to alternative method
                url = f"https://graph.microsoft.com/v1.0/users/{client.user_email}/messages?$top=10&$select=id,subject,from,receivedDateTime,bodyPreview,hasAttachments,conversationId&$orderby=receivedDateTime desc"
                response = requests.get(url, headers=headers)
                all_messages = response.json().get('value', [])
                thread_messages = [msg for msg in all_messages if msg.get('conversationId') == thread_id]
            else:
                thread_messages = response.json().get('value', [])
            
            summary = []
            for msg in thread_messages:
                has_attachments = msg.get('hasAttachments', False)
                attachment_note = " [Has attachments]" if has_attachments else ""
                
                summary.append(f"""
    From: {msg.get('from', {}).get('emailAddress', {}).get('address', 'Unknown')}
    Date: {msg.get('receivedDateTime', 'Unknown')}
    Subject: {msg.get('subject', 'No Subject')}
    Preview: {msg.get('bodyPreview', '')[:150]}...{attachment_note}
    ---
    """)
            
            return "\n".join(summary) or "No emails found in thread"
        except Exception as e:
            return f"Error processing thread: {str(e)}"
