import requests
import json
import base64
import os
import logging
import re
from typing import Dict, Any, List, Optional
from msal import ConfidentialClientApplication

def get_graph_token():
    app = ConfidentialClientApplication(
        os.getenv("MS_CLIENT_ID"),
        authority=f"https://login.microsoftonline.com/{os.getenv('MS_TENANT_ID')}",
        client_credential=os.getenv("MS_CLIENT_SECRET")
    )
    result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    if "access_token" in result:
        return result["access_token"]
    else:
        raise Exception(f"Failed to get Graph token: {result.get('error_description')}")


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EmailIntegration:
    """
    Handles the integration between processed emails and the external API endpoint.
    """
    
    def __init__(self):
        # External API configuration
        self.api_base_url = os.getenv('EXTERNAL_API_URL', 'https://tsd.dataserve.com.sa:4443/moamalat-api')
        self.api_endpoint = '/integration/correspondences/add-incoming-skill'
        self.api_url = f"{self.api_base_url}{self.api_endpoint}"
        
        # Static values for the API payload
        self.confidentiality_id = os.getenv('CONFIDENTIALITY_ID', '0')
        self.external_no = os.getenv('EXTERNAL_NO', '197')
        self.external_unit = os.getenv('EXTERNAL_UNIT', '1')
        
        # API auth token if needed
        self.api_token = os.getenv('EXTERNAL_API_TOKEN', '')
    
    def _encode_attachment(self, file_path: str) -> str:
        """
        Convert an attachment file to base64 string if the file exists.
        
        Args:
            file_path: Path to the attachment file
            
        Returns:
            Base64 encoded string of the file, or empty string if not found
        """
        if not os.path.isfile(file_path):
            logger.warning(f"Attachment not found: {file_path}")
            return ""

        try:
            with open(file_path, "rb") as file:
                encoded_string = base64.b64encode(file.read()).decode('utf-8')
                logger.info(f"Attachment encoded successfully: {file_path}")
                return encoded_string
        except Exception as e:
            logger.error(f"Error encoding attachment {file_path}: {str(e)}")
            return ""

    
    def _prepare_payload(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare the payload for the external API.
        
        Args:
            email_data: Dictionary containing processed email data
            
        Returns:
            Dictionary with formatted payload for the API
        """
        # Extract relevant data from email
        subject = email_data.get('subject', 'No Subject')
        body = email_data.get('body', 'No Content')
        
        # Format remarks from body (limit length if needed)
        max_remarks_length = 5000  # Adjust as needed
        remarks = body
        if len(remarks) > max_remarks_length:
            remarks = remarks[:max_remarks_length] + "..."
        
        # Handle attachments if present
        attachment_base64 = ""
        
        attachments = email_data.get('attachments', [])
        if attachments and len(attachments) > 0:
            # For simplicity, we'll use the first attachment only
            # Modify this logic if you need to handle multiple attachments
            first_attachment = attachments[0]
            attachment_base64 = self._encode_attachment(first_attachment)
        
        # Create payload
        payload = {
            "subject": subject,
            "confidentialityId": self.confidentiality_id,
            "externalNo": self.external_no,
            "remarks": remarks,
            "externalUnit": self.external_unit,
            "attachment": attachment_base64
        }
        
        return payload
    
    def send_to_external_api(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send processed email data to the external API.
        
        Args:
            email_data: Dictionary containing processed email data
            
        Returns:
            Dictionary with the integration result
        """
        result = {
            "success": False,
            "message": "",
            "status_code": None,
            "api_response": None
        }
        
        try:
            # Prepare the payload
            payload = self._prepare_payload(email_data)
            
            # if not payload.get("attachment"):
            #     result["message"] = "Skipped integration: No attachment to upload"
            #     logger.warning(result["message"])
            #     return result
            if not payload.get("attachment"):
                logger.warning("No attachment found; continuing with integration anyway")
            # Prepare headers
            headers = {
                "Content-Type": "application/json"
            }
            
            # Add authorization if token exists
            if self.api_token:
                headers["Authorization"] = f"Bearer {self.api_token}"
            
            # Log the request (without sensitive data)
            logger.info(f"Sending request to {self.api_url}")
            logger.info(f"Subject: {payload['subject']}")
            
            # Make the API request
            response = requests.post(
                self.api_url,
                headers=headers,
                data=json.dumps(payload),
                timeout=30  # Set a reasonable timeout
            )

            logger.info(f"Payload being sent: {json.dumps(payload, indent=2)}")

            
            # Store status code
            result["status_code"] = response.status_code
            
            # Check if the request was successful
            if response.status_code in [200, 201]:
                result["success"] = True
                result["message"] = "Successfully integrated email with external system"
                try:
                    json_response = response.json()
                    result["api_response"] = json_response

                    if "payload" in json_response and "correspondenceId" in json_response["payload"]:
                        result["correspondence_id"] = json_response["payload"]["correspondenceId"]
                        logger.info(f"Correspondence created with ID: {result['correspondence_id']}")

                        # Optional: notify sender
                        sender_email = email_data.get("sender", "")
                        if sender_email:
                            send_confirmation_email(
                                recipient_email=sender_email,
                                subject=email_data.get("subject", "Your Email"),
                                correspondence_id=result["correspondence_id"]
                            )
                except Exception as e:
                    logger.warning(f"Failed to parse JSON response: {e}")

            
        except requests.exceptions.RequestException as e:
            result["success"] = False
            result["message"] = f"Request error: {str(e)}"
            logger.error(result["message"])
        
        except Exception as e:
            result["success"] = False
            result["message"] = f"Integration error: {str(e)}"
            logger.error(result["message"])
        
        logger.info(f"Final Payload to External API:\n{json.dumps(payload, indent=2)}")
        self._last_payload = payload
        
        return result
    
    def process_emails(self, emails_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process a list of emails and send them to the external API.
        
        Args:
            emails_data: List of dictionaries containing processed email data
            
        Returns:
            List of dictionaries with integration results for each email
        """
        results = []
        
        for email in emails_data:
            logger.info(f"Processing email integration for: {email.get('subject', 'Unknown')}")
            
            # Send to external API
            integration_result = self.send_to_external_api(email)
            
            # Add email info to result for tracking
            result = {
                "email_id": email.get("id", "unknown"),
                "thread_id": email.get("threadId", "unknown"),
                "subject": email.get("subject", "No Subject"),
                "integration_result": integration_result
            }
            
            results.append(result)
        
        return results

def parse_action_required_emails(action_required_emails):
    """
    Parse the emails from action required emails data.
    """
    emails = []
    
    try:
        # Convert to string if it's not already
        if not isinstance(action_required_emails, str):
            email_text = str(action_required_emails)
        else:
            email_text = action_required_emails

        logger.info(f"Raw email text to parse:\n{email_text}")

        # Improved regex pattern for thread IDs - handle ### format from the logs
        thread_id_pattern = r'### Thread ID:?\s*([A-Za-z0-9+/=]+)'
        thread_ids = re.findall(thread_id_pattern, email_text)
        
        # If we don't find thread IDs with ###, try with ** or plain format
        if not thread_ids:
            thread_id_pattern = r'(?:\*\*)?Thread ID:?(?:\*\*)?\s*([A-Za-z0-9+/=]+)'
            thread_ids = re.findall(thread_id_pattern, email_text)
        
        # Clean thread IDs by removing any leading/trailing special characters
        thread_ids = [tid.strip(':-* ') for tid in thread_ids]
        
        logger.info(f"Found thread IDs: {thread_ids}")

        # Dump raw text to log to inspect format
        logger.info("DEBUG - Raw CrewAI output format:")
        logger.info("-" * 50)
        logger.info(email_text)
        logger.info("-" * 50)

        # For each thread ID, extract the corresponding email data
        for i, thread_id in enumerate(thread_ids):
            logger.info(f"Processing thread ID #{i+1}: {thread_id}")
            
            # Initialize email data with thread ID
            email_data = {
                "threadId": thread_id,
                "id": thread_id,
                "attachments": []
            }
            
            # Extract subject directly without splitting sections
            subject_pattern = r'\*\*Subject:\*\*\s*(.*?)(?=\n\*\*|\n$)'
            subject_match = re.search(subject_pattern, email_text)
            if subject_match:
                email_data["subject"] = subject_match.group(1).strip()
                logger.info(f"Found subject: {email_data['subject']}")
            else:
                email_data["subject"] = "Email from Thread"
                logger.info(f"No subject found, using default: {email_data['subject']}")
            
            # Extract sender
            sender_pattern = r'\*\*Sender\'s Email Address:\*\*\s*(.*?)(?=\n\*\*|\n$)'
            sender_match = re.search(sender_pattern, email_text)
            if sender_match:
                email_data["sender"] = sender_match.group(1).strip()
                logger.info(f"Found sender: {email_data['sender']}")
            else:
                logger.info("No sender found")
            
            # Extract summary
            summary_pattern = r'\*\*Summary:\*\*\s*(.*?)(?=\n\*\*Main Points|\n$)'
            summary_match = re.search(summary_pattern, email_text, re.DOTALL)
            if summary_match:
                summary = summary_match.group(1).strip()
                logger.info(f"Found summary (first 50 chars): {summary[:50]}...")
            else:
                summary = ""
                logger.info("No summary found")
            
            # Extract main points
            main_points_pattern = r'\*\*Main Points:\*\*(.*?)(?=\n\*\*Attachments|\n$)'
            main_points_match = re.search(main_points_pattern, email_text, re.DOTALL)
            if main_points_match:
                main_points = main_points_match.group(1).strip()
                logger.info(f"Found main points (first 50 chars): {main_points[:50]}...")
            else:
                main_points = ""
                logger.info("No main points found")
            
            # Combine for body
            body_parts = []
            if summary:
                body_parts.append(f"Summary: {summary}")
            if main_points:
                body_parts.append(f"Main Points: {main_points}")
            
            email_data["body"] = "\n\n".join(body_parts) if body_parts else "No content extracted"
            logger.info(f"Body length: {len(email_data['body'])} characters")
            
            # Extract attachments
            attachments_pattern = r'\*\*Attachments:\*\*\s*(.*?)(?=\n\*\*|\n$)'
            attachments_match = re.search(attachments_pattern, email_text)
            if attachments_match:
                attachments_text = attachments_match.group(1).strip()
                logger.info(f"Found attachments text: {attachments_text}")
                
                if attachments_text.lower() not in ["none", "none found"]:
                    attachments = [os.path.join("attachments", att.strip()) 
                                  for att in re.split(r'[,;]', attachments_text) 
                                  if att.strip()]
                    email_data["attachments"] = attachments
                    logger.info(f"Attachments: {attachments}")
                else:
                    logger.info("No attachments found (explicitly marked as None)")
            else:
                logger.info("No attachments section found")
            
            # Log the complete email data for debugging
            logger.info(f"Complete email data for thread ID {thread_id}:")
            logger.info(f"  - subject: {email_data.get('subject', 'N/A')}")
            logger.info(f"  - sender: {email_data.get('sender', 'N/A')}")
            logger.info(f"  - body length: {len(email_data.get('body', ''))}")
            logger.info(f"  - attachments: {email_data.get('attachments', [])}")
            
            # Add the email data if we have the minimum required fields
            if email_data.get("subject"):
                emails.append(email_data)
                logger.info(f"Added email with ThreadID={thread_id} to the list")
            else:
                logger.warning(f"Skipping email with ThreadID={thread_id} - missing required fields")
    
    except Exception as e:
        logger.error(f"Error parsing emails: {str(e)}", exc_info=True)
    
    logger.info(f"Successfully parsed {len(emails)} emails for integration")
    return emails

def is_valid_thread_id(thread_id: str) -> bool:
    """Validate Microsoft Graph thread/conversation ID format"""
    if not thread_id:
        return False
    # Basic validation - adjust based on your actual ID patterns
    return len(thread_id) > 20 and all(c.isalnum() or c in {'-', '_', '=', '+', '/'} for c in thread_id)

# Main integration function
def integrate_emails(action_required_emails):
    """
    Process emails and send them to external API.
    
    Args:
        action_required_emails: Output from the email processing step
        
    Returns:
        Dictionary with integration results
    """
    try:
        # Improved logging
        logger.info(f"Starting integration process with action_required_emails type: {type(action_required_emails)}")
        if isinstance(action_required_emails, str):
            logger.info(f"Action required emails preview: {action_required_emails[:500]}...")
        
        # Parse the email data with our improved parser
        emails = parse_action_required_emails(action_required_emails)
        
        # Log the number of emails parsed
        logger.info(f"Parser returned {len(emails)} emails")
        for i, email in enumerate(emails):
            logger.info(f"Email {i+1} details:")
            logger.info(f"  - ThreadID: {email.get('threadId', 'Unknown')}")
            logger.info(f"  - Subject: {email.get('subject', 'Unknown')}")
            logger.info(f"  - Sender: {email.get('sender', 'Unknown')}")
            logger.info(f"  - Body length: {len(email.get('body', ''))}")
            logger.info(f"  - Attachments: {email.get('attachments', [])}")
        
        valid_emails = []
        for email in emails:
            if not is_valid_thread_id(email.get('threadId', '')):
                logger.warning(f"Skipping email with invalid thread ID: {email.get('threadId')}")
                continue
            valid_emails.append(email)
            
        logger.info(f"After validation, {len(valid_emails)} valid emails remain")
        
        if not valid_emails:
            logger.warning("No valid emails found after thread ID validation")
            return {
                "success": False,
                "message": "No valid emails found (invalid thread IDs)",
                "results": []
            }
        
        logger.info(f"Successfully parsed {len(valid_emails)} valid emails for integration")
        for i, email in enumerate(valid_emails):
            logger.info(f"Valid Email {i+1}: ThreadID={email.get('threadId')}, Subject={email.get('subject')}")
        
        # Inject downloaded attachments into email data
        for email in valid_emails:
            thread_id = email.get("threadId")
            if thread_id:
                logger.info(f"Fetching attachments for thread ID: {thread_id}")
                attachments = fetch_attachments_from_graph(thread_id)
                if attachments:
                    email["attachments"] = attachments
                    logger.info(f"Added {len(attachments)} attachments to email: {attachments}")
                else:
                    logger.info(f"No attachments found for thread ID: {thread_id}")
        
        # Initialize the integration service
        logger.info("Initializing EmailIntegration service")
        integration = EmailIntegration()
        
        # Process the emails
        logger.info(f"Processing {len(valid_emails)} emails with EmailIntegration")
        results = integration.process_emails(valid_emails)
        
        # Calculate success status
        success_count = sum(1 for r in results if r.get("integration_result", {}).get("success", False))
        total_count = len(results)
        
        logger.info(f"Integration complete: {success_count}/{total_count} successful")
        
        return {
            "success": success_count > 0,
            "message": f"Processed {total_count} emails, {success_count} integrated successfully",
            "results": results
        }
    
    except Exception as e:
        logger.error(f"Error in email integration process: {str(e)}", exc_info=True)
        return {
            "success": False,
            "message": f"Integration failed: {str(e)}",
            "results": []
        }
    
def fetch_attachments_from_graph(thread_id: str, save_dir: str = "attachments") -> List[str]:
    """
    Fetch and save all attachments from a given email thread via MS Graph API.
    Returns a list of local file paths.
    """
    # Clean the thread ID first
    thread_id = thread_id.strip(':-* ')
    
    if not thread_id:
        logger.error("Empty thread ID provided")
        return []
        
    logger.info(f"Fetching attachments for thread: {thread_id}")
    os.makedirs(save_dir, exist_ok=True)
    
    try:
        access_token = get_graph_token()
        if not access_token:
            logger.error("Failed to get Graph token")
            return []
            
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        user_email = os.getenv("MS_USER_EMAIL")
        
        # First, try to use thread_id as message ID to get conversation ID
        try:
            message_endpoint = f"https://graph.microsoft.com/v1.0/users/{user_email}/messages/{thread_id}"
            message_response = requests.get(message_endpoint, headers=headers)
            
            if message_response.status_code == 200:
                # Successfully fetched message, use its conversationId
                conversation_id = message_response.json().get("conversationId")
                if conversation_id:
                    logger.info(f"Found conversationId from message: {conversation_id}")
                    endpoint = f"https://graph.microsoft.com/v1.0/users/{user_email}/messages?$filter=conversationId eq '{conversation_id}'"
                else:
                    # Fallback to using thread_id directly as conversationId
                    logger.warning("No conversationId found in message, using thread_id as conversationId")
                    endpoint = f"https://graph.microsoft.com/v1.0/users/{user_email}/messages?$filter=conversationId eq '{thread_id}'"
            else:
                # Failed to fetch message, thread_id might be a conversationId already
                logger.warning(f"Failed to fetch message using thread_id as messageId: {message_response.status_code}")
                endpoint = f"https://graph.microsoft.com/v1.0/users/{user_email}/messages?$filter=conversationId eq '{thread_id}'"
        except Exception as e:
            logger.warning(f"Error when trying to get conversationId: {str(e)}")
            # Fallback to using thread_id directly as conversationId
            endpoint = f"https://graph.microsoft.com/v1.0/users/{user_email}/messages?$filter=conversationId eq '{thread_id}'"

        # Fetch messages in the conversation
        response = requests.get(endpoint, headers=headers)
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch messages: {response.text}")
            return []

        messages = response.json().get("value", [])
        downloaded_files = []

        for message in messages:
            msg_id = message.get("id")
            if not msg_id:
                continue
                
            attachment_url = f"https://graph.microsoft.com/v1.0/users/{user_email}/messages/{msg_id}/attachments"
            att_resp = requests.get(attachment_url, headers=headers)

            if att_resp.status_code != 200:
                logger.warning(f"No attachments found for message {msg_id}")
                continue

            for attachment in att_resp.json().get("value", []):
                if attachment.get("@odata.type") == "#microsoft.graph.fileAttachment":
                    filename = attachment.get("name")
                    content_bytes = attachment.get("contentBytes")

                    if not filename or not content_bytes:
                        continue

                    # Sanitize filename
                    filename = "".join(c for c in filename if c.isalnum() or c in (' ', '.', '_', '-')).rstrip()
                    file_path = os.path.join(save_dir, filename)
                    
                    try:
                        with open(file_path, "wb") as f:
                            f.write(base64.b64decode(content_bytes))
                        downloaded_files.append(file_path)
                        logger.info(f"Downloaded attachment: {file_path}")
                    except Exception as e:
                        logger.error(f"Failed to save attachment {filename}: {e}")
        
        return downloaded_files
        
    except Exception as e:
        logger.error(f"Error fetching attachments: {e}")
        return []

def send_confirmation_email(recipient_email: str, subject: str, correspondence_id: str):
    """
    Sends a confirmation email to the sender with the created correspondence ID.
    """
    try:
        access_token = get_graph_token()
        user_email = os.getenv("MS_USER_EMAIL")
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        body = {
            "message": {
                "subject": f"📬 Your email has been processed: {subject}",
                "body": {
                    "contentType": "Text",
                    "content": f"Your correspondence has been successfully processed.\n\nCorrespondence ID: {correspondence_id}\n\nThank you."
                },
                "toRecipients": [
                    {
                        "emailAddress": {
                            "address": recipient_email
                        }
                    }
                ]
            },
            "saveToSentItems": "true"
        }

        endpoint = f"https://graph.microsoft.com/v1.0/users/{user_email}/sendMail"
        response = requests.post(endpoint, headers=headers, json=body)

        if response.status_code in [202]:
            logger.info(f"Confirmation email sent to: {recipient_email}")
        else:
            logger.warning(f"Failed to send confirmation email: {response.status_code}, {response.text}")
    
    except Exception as e:
        logger.error(f"Error sending confirmation email: {e}")