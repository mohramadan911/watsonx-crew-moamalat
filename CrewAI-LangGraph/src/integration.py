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
    
    Args:
        action_required_emails: String, dictionary, or CrewAI output containing email data
        
    Returns:
        List of dictionaries with parsed email data
    """
    emails = []
    
    try:
        # Handle CrewAI output
        if str(type(action_required_emails)).find('crewai.crews.crew_output.CrewOutput') != -1:
            logger.info("Parsing CrewOutput from CrewAI")
            
            # Convert CrewOutput to string to extract data
            crew_output_str = str(action_required_emails)
            logger.info(f"CrewOutput preview: {crew_output_str[:500]}...")
            
            # Try to extract email data from the Email Action Specialist's output
            # Look for thread IDs in the final answer
            thread_ids = re.findall(r'Thread ID:?\s*([A-Za-z0-9+=\/]+)', crew_output_str)
            logger.info(f"Found {len(thread_ids)} thread IDs: {thread_ids}")
            
            # Look for email summaries
            email_sections = re.split(r'\d+\.\s+\*\*Thread ID:\*\*', crew_output_str)
            if len(email_sections) <= 1:
                # Try alternative pattern
                email_sections = re.split(r'Thread ID:', crew_output_str)[1:]
            
            # Process each section
            for i, section in enumerate(email_sections):
                if i >= len(thread_ids):
                    continue
                    
                thread_id = thread_ids[i]
                
                email_data = {
                    "threadId": thread_id,
                    "id": thread_id
                }
                
                # Extract subject
                subject_match = re.search(r'Summary:?\s*(.*?)(?=\n|\*\*|$)', section)
                if subject_match:
                    email_data["subject"] = subject_match.group(1).strip()
                else:
                    email_data["subject"] = "Email from CrewAI Analysis"
                
                # Extract sender
                sender_match = re.search(r'Sender\'s Email Address:?\s*(.*?)(?=\n|\*\*|$)', section)
                if not sender_match:
                    sender_match = re.search(r'Sender:?\s*(.*?)(?=\n|\*\*|$)', section)
                
                if sender_match:
                    email_data["sender"] = sender_match.group(1).strip()
                
                # Extract body content
                body_parts = []
                
                # Find main points
                main_points_match = re.search(r'Main Points:(.*?)(?=\*\*|$)', section, re.DOTALL)
                if main_points_match:
                    body_parts.append(f"Main Points: {main_points_match.group(1).strip()}")
                
                # Find summary
                summary_match = re.search(r'Summary:(.*?)(?=\*\*|Main Points:|$)', section, re.DOTALL)
                if summary_match:
                    body_parts.append(f"Summary: {summary_match.group(1).strip()}")
                
                # If no specific parts found, use the whole section
                if not body_parts:
                    body_parts.append(section.strip())
                
                email_data["body"] = "\n\n".join(body_parts)
                
                # Extract attachments
                email_data["attachments"] = []
                attachment_match = re.search(r'Attachments:?\s*(.*?)(?=\n\*\*|$)', section, re.DOTALL)
                if attachment_match:
                    attachments_text = attachment_match.group(1).strip()
                    if attachments_text.lower() != "none" and attachments_text.lower() != "none found":
                        att_list = attachments_text.split(",")
                        email_data["attachments"] = [att.strip() for att in att_list if att.strip()]
                
                # Only add if we have the minimum required data
                if email_data.get("threadId") and email_data.get("subject"):
                    emails.append(email_data)
                    logger.info(f"Added email with Thread ID: {email_data['threadId']}")

        # If action_required_emails is a string, parse it
        elif isinstance(action_required_emails, str):
            logger.info("Parsing string output from CrewAI")
            
            # Split by predefined separators or use newlines as fallback
            thread_sections = [action_required_emails]
            
            # Process each section
            for section in thread_sections:
                if not section.strip():
                    continue
                
                logger.info(f"Processing section: {section[:100]}...")
                
                email_data = {}
                
                # Extract Thread ID
                # thread_id_match = re.search(r'\*\*Thread ID:\*\*\s+(.*?)(?=\s+\-|\s+\*\*|\n)', section)
                thread_id_match = re.search(r'\*\*?Thread ID:?[\*\s]*\**\s*(.*?)\s*(?=\n|\*\*|\-)', section)
                if thread_id_match:
                    email_data["threadId"] = thread_id_match.group(1).strip()
                    logger.info(f"Found thread ID: {email_data['threadId']}")
                
                # Extract Subject (if available)
                subject_match = re.search(r'\*\*Summary:\*\*\s+(.*?)(?=\s+\-|\s+\*\*|\n)', section)
                if subject_match:
                    email_data["subject"] = subject_match.group(1).strip()
                elif "financial regulations" in section.lower():
                    email_data["subject"] = "Financial Regulations Discussion"
                elif "project" in section.lower() and "timelines" in section.lower():
                    email_data["subject"] = "Project Status Update"
                elif "technical" in section.lower():
                    email_data["subject"] = "Technical Integration Issues"
                else:
                    email_data["subject"] = "Email Discussion"
                
                logger.info(f"Using subject: {email_data.get('subject')}")
                
                # Extract sender email
                sender_match = re.search(r'\*\*Sender\'s Email Address:\*\*\s+(.*?)(?=\s+\-|\s+\*\*|\n)', section)
                if sender_match:
                    email_data["sender"] = sender_match.group(1).strip()
                
                # Extract main points for body
                body_parts = []
                
                # Add summary if available
                summary_match = re.search(r'\*\*Summary:\*\*\s+(.*?)(?=\s+\-|\s+\*\*|\n)', section)
                if summary_match:
                    body_parts.append(f"Summary: {summary_match.group(1).strip()}")
                
                # Add main points if available
                main_points_section = re.search(r'\*\*Main Points:\*\*(.*?)(?=\s+\*\*|\Z)', section, re.DOTALL)
                if main_points_section:
                    body_parts.append(f"Main Points: {main_points_section.group(1).strip()}")
                
                # Use the whole section as body if nothing specific was found
                if not body_parts:
                    body_parts.append(section.strip())
                
                email_data["body"] = "\n\n".join(body_parts)
                
                # Extract attachments (if any)
                attachments = []
                if "Attachments downloaded:" in section or "📎" in section:
                    for line in section.split("\n"):
                        if "Attachments downloaded:" in line or "📎" in line:
                            att_parts = line.split(":", 1)
                            if len(att_parts) > 1:
                                att_list = att_parts[1].strip().split(",")
                                for att in att_list:
                                    clean_att = att.strip()
                                    if clean_att:
                                        # Assume saved to attachments/ directory
                                        attachments.append(os.path.join("attachments", clean_att))

                email_data["attachments"] = attachments

                
                # Only add to list if we have the minimum required data
                if email_data.get("threadId") and email_data.get("subject"):
                    # Add some identifiers for the API payload
                    email_data["id"] = email_data.get("threadId")
                    emails.append(email_data)
                    logger.info(f"Added email with Thread ID: {email_data['threadId']}")
        
        # Handle structured output if available
        elif isinstance(action_required_emails, dict):
            logger.info("Parsing dictionary output from CrewAI")
            
            # Handle structured data - logic would depend on actual structure
            # This is a placeholder for future implementation
            pass
    
    except Exception as e:
        logger.error(f"Error parsing action required emails: {str(e)}")
        logger.error(f"Exception details: {e}", exc_info=True)
    
    logger.info(f"Parsed {len(emails)} emails for integration")
    return emails

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
        
        if not emails:
            logger.warning("No emails parsed for integration")
            return {
                "success": False,
                "message": "No valid emails found for integration",
                "results": []
            }
        
        logger.info(f"Successfully parsed {len(emails)} emails for integration")
        for i, email in enumerate(emails):
            logger.info(f"Email {i+1}: ThreadID={email.get('threadId')}, Subject={email.get('subject')}")
        
        # Inject downloaded attachments into email data
        for email in emails:
            thread_id = email.get("threadId")
            if thread_id:
                email["attachments"] = fetch_attachments_from_graph(thread_id)
        # Initialize the integration service
        integration = EmailIntegration()
        
        # Process the emails
        results = integration.process_emails(emails)
        
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
        logger.error(f"Error in email integration process: {str(e)}")
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
    logger.info(f"Fetching attachments for thread: {thread_id}")
    os.makedirs(save_dir, exist_ok=True)
    access_token = get_graph_token()
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    user_email = os.getenv("MS_USER_EMAIL")
    endpoint = f"https://graph.microsoft.com/v1.0/users/{user_email}/messages?$filter=conversationId eq '{thread_id}'"


    response = requests.get(endpoint, headers=headers)

    if response.status_code != 200:
        logger.error(f"Failed to fetch messages: {response.text}")
        return []

    messages = response.json().get("value", [])
    downloaded_files = []

    for message in messages:
        msg_id = message.get("id")
        attachment_url = f"https://graph.microsoft.com/v1.0/users/{user_email}/messages/{msg_id}/attachments"

        att_resp = requests.get(attachment_url, headers=headers)

        if att_resp.status_code != 200:
            logger.warning(f"No attachments found for message {msg_id}")
            continue

        for attachment in att_resp.json().get("value", []):
            if attachment.get("@odata.type") == "#microsoft.graph.fileAttachment":
                filename = attachment["name"]
                content_bytes = attachment["contentBytes"]

                file_path = os.path.join(save_dir, filename)
                try:
                    with open(file_path, "wb") as f:
                        f.write(base64.b64decode(content_bytes))
                    downloaded_files.append(file_path)
                    logger.info(f"Downloaded attachment: {file_path}")
                except Exception as e:
                    logger.error(f"Failed to save attachment {filename}: {e}")
    
    return downloaded_files

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
