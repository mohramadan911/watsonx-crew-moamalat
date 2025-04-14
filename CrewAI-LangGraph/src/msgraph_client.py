import msal
import requests
import base64
import logging
import os
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MSGraphClient:
    def __init__(self, client_id, client_secret, tenant_id, user_email):
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.user_email = user_email
        self.access_token = None
        self.scopes = ['https://graph.microsoft.com/.default']

    def get_token(self):
        app = msal.ConfidentialClientApplication(
            self.client_id,
            authority=f"https://login.microsoftonline.com/{self.tenant_id}",
            client_credential=self.client_secret
        )
        result = app.acquire_token_for_client(scopes=self.scopes)
        if "access_token" in result:
            self.access_token = result["access_token"]
            return True
        logger.error(f"Token error: {result}")
        return False

    def send_email(self, to_email, subject, body):
        if not self.access_token and not self.get_token():
            return False
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # Add debug logging
        print(f"Attempting to create draft email to: {to_email}")
        
        try:
            email_message = {
                "subject": subject,
                "body": {"contentType": "HTML", "content": body},
                "toRecipients": [{"emailAddress": {"address": to_email}}]
            }
            
            # For creating a draft instead of sending
            url = f"https://graph.microsoft.com/v1.0/users/{self.user_email}/messages"
            
            # Log the request details
            print(f"API URL for creating draft: {url}")
            
            response = requests.post(url, headers=headers, json=email_message)
            
            # Log the response
            print(f"Draft creation response: {response.status_code}")
            print(f"Response content: {response.text[:500]}...")
            
            # If successful, the message should be created but not sent
            if response.status_code in [200, 201]:
                return True
            else:
                print(f"Failed to create draft: {response.text}")
                return False
        
        except Exception as e:
            print(f"Exception in send_email: {str(e)}")
            return False