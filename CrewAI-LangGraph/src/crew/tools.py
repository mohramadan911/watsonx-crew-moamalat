# tools.py
from langchain.tools import tool
from src.msgraph_client import MSGraphClient
import os
import requests
from src.utils.attachment_summary import summarize_attachments_with_gpt

def download_attachment(client, message_id, attachment_id, filename, save_dir="attachments"):
    os.makedirs(save_dir, exist_ok=True)
    headers = {"Authorization": f"Bearer {client.access_token}"}
    url = f"https://graph.microsoft.com/v1.0/users/{client.user_email}/messages/{message_id}/attachments/{attachment_id}/$value"
    response = requests.get(url, headers=headers)

    if response.ok:
        filepath = os.path.join(save_dir, filename)
        with open(filepath, "wb") as f:
            f.write(response.content)
        return filepath
    return None

class EmailThreadTool():
    @tool("Fetch Email Thread")
    def fetch_thread(thread_id: str):
        """
        Fetch email thread summary with attachment info.
        """
        client = MSGraphClient(
            client_id=os.environ['MS_CLIENT_ID'],
            client_secret=os.environ['MS_CLIENT_SECRET'],
            tenant_id=os.environ['MS_TENANT_ID'],
            user_email=os.environ['MS_USER_EMAIL']
        )

        if not client.get_token():
            return "❌ Unable to retrieve Microsoft Graph token"

        headers = {"Authorization": f"Bearer {client.access_token}"}
        url = (
            f"https://graph.microsoft.com/v1.0/users/{client.user_email}/messages"
            f"?$filter=conversationId eq '{thread_id}'"
            f"&$select=id,subject,from,receivedDateTime,bodyPreview,hasAttachments"
            f"&$top=10&$orderby=receivedDateTime desc"
        )

        try:
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                return f"❌ Graph API error {response.status_code}: {response.text}"

            thread_messages = response.json().get('value', [])
            if not thread_messages:
                return "⚠️ No emails found in this thread"

            summary = []
            for msg in thread_messages:
                has_attachments = msg.get('hasAttachments', False)
                attachment_paths = []

                if has_attachments:
                    attach_url = f"https://graph.microsoft.com/v1.0/users/{client.user_email}/messages/{msg['id']}/attachments"
                    attach_resp = requests.get(attach_url, headers=headers).json()

                    for att in attach_resp.get("value", []):
                        if att.get('@odata.type') == "#microsoft.graph.fileAttachment":
                            filename = att.get("name")
                            attachment_id = att.get("id")
                            local_path = download_attachment(client, msg['id'], attachment_id, filename)
                            if local_path:
                                attachment_paths.append(local_path)

                if attachment_paths:
                    summary.append(f"📎 Attachments downloaded: {', '.join(os.path.basename(p) for p in attachment_paths)}")
                    try:
                        att_summary, link_summary = summarize_attachments_with_gpt(attachment_paths)
                        summary.append(att_summary)
                        summary.append(f"🔗 Link Safety Review:\n{link_summary}")
                    except Exception as e:
                        summary.append(f"⚠️ Attachment processing error: {str(e)}")

                attachment_note = f" [Has attachments: {', '.join(os.path.basename(p) for p in attachment_paths)}]" if attachment_paths else ""

                summary.append(f"""
    From: {msg.get('from', {}).get('emailAddress', {}).get('address', 'Unknown')}
    Date: {msg.get('receivedDateTime', 'Unknown')}
    Subject: {msg.get('subject', 'No Subject')}
    Preview: {msg.get('bodyPreview', '')[:150]}...{attachment_note}
    ---
    """)

            return "\n".join(summary)

        except Exception as e:
            return f"❌ Error processing thread: {str(e)}"

        
email_thread_tool = EmailThreadTool().fetch_thread