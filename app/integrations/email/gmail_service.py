"""
Gmail Service

Wrapper for Gmail API operations: send, read, search, draft emails.

Handles authentication, API calls, and error handling for Gmail integration.
"""

from typing import List, Dict, Any, Optional
import logging
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.integrations.base_integration import BaseIntegration
from app.exceptions import EmailServiceError, NotAuthenticatedError

logger = logging.getLogger(__name__)


class GmailService(BaseIntegration):
    """
    Gmail API service for email operations.
    
    Provides methods to:
    - Send emails
    - Read emails
    - Search emails
    - Draft emails
    - Reply to emails
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Gmail service.
        
        Args:
            config: Configuration with credentials
        """
        self.config = config
        self.is_authenticated = False
        self.service = None
        self.scopes = [
            'https://www.googleapis.com/auth/gmail.send',
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/gmail.modify',
            'https://www.googleapis.com/auth/gmail.compose'
        ]
    
    async def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """
        Authenticate with Gmail API.
        
        Args:
            credentials: OAuth2 credentials dict
            
        Returns:
            True if authentication successful
        """
        try:
            creds = Credentials(
                token=credentials.get('token'),
                refresh_token=credentials.get('refresh_token'),
                token_uri=credentials.get('token_uri'),
                client_id=credentials.get('client_id'),
                client_secret=credentials.get('client_secret'),
                scopes=self.scopes
            )
            
            self.service = build('gmail', 'v1', credentials=creds)
            self.is_authenticated = True
            
            logger.info("Gmail service authenticated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Gmail authentication failed: {e}")
            self.is_authenticated = False
            return False
    
    async def health_check(self) -> bool:
        """
        Check if Gmail service is accessible.
        
        Returns:
            True if service is healthy
        """
        if not self.is_authenticated or not self.service:
            return False
        
        try:
            # Try to get user profile as health check
            self.service.users().getProfile(userId='me').execute()
            return True
        except Exception as e:
            logger.error(f"Gmail health check failed: {e}")
            return False
    
    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Send an email via Gmail.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (HTML or plain text)
            cc: List of CC recipients
            bcc: List of BCC recipients
            attachments: List of attachment dicts with 'filename' and 'content'
            
        Returns:
            Response dict with message ID and status
        """
        if not self.is_authenticated:
            raise NotAuthenticatedError("Gmail")
        
        if not self.service:
            raise EmailServiceError("Gmail service not initialized")
        
        try:
            # Create message
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject
            
            if cc:
                message['cc'] = ', '.join(cc)
            if bcc:
                message['bcc'] = ', '.join(bcc)
            
            # Add body
            message.attach(MIMEText(body, 'html' if '<html>' in body.lower() else 'plain'))
            
            # Add attachments
            if attachments:
                for attachment in attachments:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment['content'])
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f"attachment; filename= {attachment['filename']}"
                    )
                    message.attach(part)
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Send
            sent_message = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            logger.info(f"Email sent successfully: {sent_message['id']}")
            
            return {
                'success': True,
                'message_id': sent_message['id'],
                'thread_id': sent_message.get('threadId'),
                'label_ids': sent_message.get('labelIds', [])
            }
            
        except HttpError as e:
            logger.error(f"Gmail API error sending email: {e}")
            raise EmailServiceError(f"Failed to send email: {str(e)}", original_error=e)
    
    async def read_emails(
        self,
        max_results: int = 10,
        query: Optional[str] = None,
        label_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Read emails from Gmail.
        
        Args:
            max_results: Maximum number of emails to retrieve
            query: Gmail search query (e.g., 'is:unread', 'from:user@example.com')
            label_ids: List of label IDs to filter by
            
        Returns:
            List of email dicts with id, subject, from, snippet, body
        """
        if not self.is_authenticated:
            raise NotAuthenticatedError("Gmail")
        
        if not self.service:
            raise EmailServiceError("Gmail service not initialized")
        
        try:
            # List messages
            list_params = {
                'userId': 'me',
                'maxResults': max_results
            }
            
            if query:
                list_params['q'] = query
            if label_ids:
                list_params['labelIds'] = label_ids
            
            results = self.service.users().messages().list(**list_params).execute()
            messages = results.get('messages', [])
            
            # Get full message details
            emails = []
            for msg in messages:
                full_msg = self.service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='full'
                ).execute()
                
                # Parse headers
                headers = {h['name']: h['value'] for h in full_msg['payload']['headers']}
                
                # Get body
                body = self._get_message_body(full_msg['payload'])
                
                emails.append({
                    'id': full_msg['id'],
                    'thread_id': full_msg['threadId'],
                    'subject': headers.get('Subject', ''),
                    'from': headers.get('From', ''),
                    'to': headers.get('To', ''),
                    'date': headers.get('Date', ''),
                    'snippet': full_msg.get('snippet', ''),
                    'body': body,
                    'label_ids': full_msg.get('labelIds', [])
                })
            
            logger.info(f"Retrieved {len(emails)} emails")
            return emails
            
        except HttpError as e:
            logger.error(f"Gmail API error reading emails: {e}")
            raise EmailServiceError(f"Failed to read emails: {str(e)}", original_error=e)
    
    def _get_message_body(self, payload: Dict[str, Any]) -> str:
        """
        Extract message body from payload.
        
        Args:
            payload: Message payload from Gmail API
            
        Returns:
            Decoded message body
        """
        if 'parts' in payload:
            # Multipart message
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data', '')
                    return base64.urlsafe_b64decode(data).decode('utf-8')
                elif part['mimeType'] == 'text/html':
                    data = part['body'].get('data', '')
                    return base64.urlsafe_b64decode(data).decode('utf-8')
        else:
            # Simple message
            data = payload['body'].get('data', '')
            if data:
                return base64.urlsafe_b64decode(data).decode('utf-8')
        
        return ''
    
    async def search_emails(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search emails using Gmail query syntax.
        
        Args:
            query: Gmail search query
            max_results: Maximum results to return
            
        Returns:
            List of matching emails
        """
        return await self.read_emails(max_results=max_results, query=query)
    
    async def reply_to_email(
        self,
        message_id: str,
        body: str,
        quote_original: bool = True
    ) -> Dict[str, Any]:
        """
        Reply to an email.
        
        Args:
            message_id: ID of message to reply to
            body: Reply body
            quote_original: Whether to quote original message
            
        Returns:
            Response dict with new message ID
        """
        if not self.is_authenticated:
            raise NotAuthenticatedError("Gmail")
        
        if not self.service:
            raise EmailServiceError("Gmail service not initialized")
        
        try:
            # Get original message
            original = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            headers = {h['name']: h['value'] for h in original['payload']['headers']}
            
            # Create reply
            reply = MIMEText(body)
            reply['to'] = headers.get('From', '')
            reply['subject'] = f"Re: {headers.get('Subject', '')}"
            reply['In-Reply-To'] = headers.get('Message-ID', '')
            reply['References'] = headers.get('Message-ID', '')
            
            # Encode and send
            raw_reply = base64.urlsafe_b64encode(reply.as_bytes()).decode('utf-8')
            
            sent_message = self.service.users().messages().send(
                userId='me',
                body={
                    'raw': raw_reply,
                    'threadId': original['threadId']
                }
            ).execute()
            
            logger.info(f"Reply sent: {sent_message['id']}")
            
            return {
                'success': True,
                'message_id': sent_message['id'],
                'thread_id': sent_message['threadId']
            }
            
        except HttpError as e:
            logger.error(f"Gmail API error replying to email: {e}")
            raise EmailServiceError(f"Failed to reply to email: {str(e)}", original_error=e)
    
    async def get_user_info(self) -> Dict[str, Any]:
        """
        Get authenticated user's Gmail profile info.
        
        Returns:
            User profile dict with email address and total messages
        """
        if not self.is_authenticated:
            raise NotAuthenticatedError("Gmail")
        
        if not self.service:
            raise EmailServiceError("Gmail service not initialized")
        
        try:
            profile = self.service.users().getProfile(userId='me').execute()
            
            return {
                'email_address': profile.get('emailAddress'),
                'messages_total': profile.get('messagesTotal'),
                'threads_total': profile.get('threadsTotal'),
                'history_id': profile.get('historyId')
            }
            
        except HttpError as e:
            logger.error(f"Gmail API error getting user info: {e}")
            raise EmailServiceError(f"Failed to get user info: {str(e)}", original_error=e)
