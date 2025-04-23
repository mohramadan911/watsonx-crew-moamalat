import os
import requests
from dotenv import load_dotenv
from src.msgraph_client import MSGraphClient

load_dotenv()

def test_graph_attachment_fetching():
    print("🔧 Running test: Graph Attachment Fetching")

    # Initialize MS Graph client
    client = MSGraphClient(
        client_id=os.environ['MS_CLIENT_ID'],
        client_secret=os.environ['MS_CLIENT_SECRET'],
        tenant_id=os.environ['MS_TENANT_ID'],
        user_email=os.environ['MS_USER_EMAIL']
    )

    if not client.get_token():
        print("❌ Failed to authenticate with Microsoft Graph")
        return

    headers = {"Authorization": f"Bearer {client.access_token}"}

    # Step 1: List the last 10 messages to extract conversation IDs
    print("📨 Fetching last 10 messages to inspect valid conversation IDs")
    list_url = f"https://graph.microsoft.com/v1.0/users/{client.user_email}/messages?$top=10&$orderby=receivedDateTime desc"
    resp = requests.get(list_url, headers=headers)

    if resp.status_code != 200:
        print(f"❌ Failed to list messages: {resp.text}")
        return

    messages = resp.json().get("value", [])
    for idx, msg in enumerate(messages):
        print(f"{idx + 1}. Subject: {msg.get('subject')}")
        print(f"   Message ID: {msg.get('id')}")
        print(f"   Conversation ID: {msg.get('conversationId')}")
        print("---")

    # Step 2: Replace this with a valid conversation ID from above
    conversation_id = "AAQkADkyN2M3N2MyLWQ1MTktNDNjNS05NGY1LTM2MzMxZTgxMTM2ZQAQAMHFHXcKt6pEoPO5tOmIM2E="
    print(f"\n📡 Requesting messages for conversation: {conversation_id}")

    url = f"https://graph.microsoft.com/v1.0/users/{client.user_email}/messages?$filter=conversationId eq '{conversation_id}'"
    resp = requests.get(url, headers=headers)

    if resp.status_code != 200:
        print(f"❌ Failed to get messages in conversation: {resp.text}")
        return

    thread_messages = resp.json().get("value", [])
    print(f"✅ Found {len(thread_messages)} messages in conversation thread")

    for msg in thread_messages:
        msg_id = msg["id"]
        print(f"\n🔍 Checking message: {msg_id}")
        att_url = f"https://graph.microsoft.com/v1.0/users/{client.user_email}/messages/{msg_id}/attachments"
        att_resp = requests.get(att_url, headers=headers)

        if att_resp.status_code != 200:
            print(f"⚠️ No attachments or error for message {msg_id}")
            continue

        attachments = att_resp.json().get("value", [])
        if not attachments:
            print("📭 No attachments found")
        else:
            for att in attachments:
                print(f"📎 Attachment Found: {att['name']} (ID: {att['id']})")

if __name__ == "__main__":
    test_graph_attachment_fetching()
