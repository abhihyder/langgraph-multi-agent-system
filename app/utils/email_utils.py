"""
Reusable utilities for email operations.

This module contains helper functions and classes that can be used
across different email-related agents and nodes.
"""

from typing import Dict, Any, Optional, List, TYPE_CHECKING
import json
from email.utils import parseaddr

if TYPE_CHECKING:
    from ..integrations.email.gmail_service import GmailService


# ========== Validation Utilities ==========

def validate_email_address(email: str) -> bool:
    """Validate email address format."""
    if not email:
        return False
    name, addr = parseaddr(email)
    return bool(addr and "@" in addr)


class EmailValidator:
    """Reusable email parameter validator."""
    
    @staticmethod
    def validate_send_params(params: Dict[str, Any]) -> Optional[str]:
        """Validate send email parameters."""
        if not params.get("to"):
            return "Missing required parameter: 'to' (recipient email)"
        
        recipients = params.get("to", [])
        if isinstance(recipients, str):
            recipients = [recipients]
        
        for recipient in recipients:
            if not validate_email_address(recipient):
                return f"Invalid email address: {recipient}"
        return None
    
    @staticmethod
    def validate_reply_params(params: Dict[str, Any]) -> Optional[str]:
        """Validate reply parameters."""
        if not params.get("message_id"):
            return "Missing required parameter: 'message_id' for reply"
        return None
    
    @staticmethod
    def validate_search_params(params: Dict[str, Any]) -> Optional[str]:
        """Validate search parameters."""
        if not params.get("query"):
            return "Missing required parameter: 'query' for search"
        return None
    
    @staticmethod
    def validate_by_action(action: str, params: Dict[str, Any]) -> Optional[str]:
        """Validate parameters based on action type."""
        validators = {
            "send": EmailValidator.validate_send_params,
            "reply": EmailValidator.validate_reply_params,
            "search": EmailValidator.validate_search_params,
            "summarize": lambda p: EmailValidator.validate_reply_params(p),
            "extract_actions": lambda p: EmailValidator.validate_reply_params(p)
        }
        
        validator = validators.get(action)
        if validator:
            return validator(params)
        return None


# ========== Parsing Utilities ==========

def parse_llm_json_response(content: str) -> Dict[str, Any]:
    """Parse JSON from LLM response, handling code blocks."""
    content = content.strip()
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
    return json.loads(content)


# ========== Formatting Utilities ==========

def format_error_message(error_type: str, error_msg: str, action: str) -> str:
    """Format error message with helpful hints."""
    output = f"❌ Email operation failed:\n\n"
    output += f"Error Type: {error_type}\n"
    output += f"Action: {action}\n"
    output += f"Details: {error_msg}\n\n"
    
    # Add helpful hints
    hints = {
        "AuthenticationError": "💡 Tip: Complete Gmail OAuth2 flow at /auth/gmail/login",
        "ValidationError": "💡 Tip: Check that all required parameters are provided and valid",
        "GmailAPIError": "💡 Tip: Check Gmail API quota and credentials",
        "IntentParsingError": "💡 Tip: Rephrase your request more clearly",
        "CompositionError": "💡 Tip: Try providing more details about the email content"
    }
    
    if error_type in hints:
        output += hints[error_type]
    
    return output


def format_gmail_list_response(messages: List[Dict], action: str, max_display: int = 5) -> str:
    """Format Gmail message list responses (read/search)."""
    if not messages:
        return f"No emails found for {action} operation."
    
    icon = "📧" if action == "read" else "🔍"
    verb = "Retrieved" if action == "read" else "Found"
    
    output = f"{icon} {verb} {len(messages)} emails:\n\n"
    
    for msg in messages[:max_display]:
        output += f"- From: {msg.get('from', 'Unknown')}\n"
        output += f"  Subject: {msg.get('subject', 'No subject')}\n"
        if action == "read":
            output += f"  Date: {msg.get('date', 'Unknown')}\n"
        output += "\n"
    
    if len(messages) > max_display:
        output += f"... and {len(messages) - max_display} more emails\n"
    
    return output


# ========== Gmail Operation Executor ==========

class GmailOperationExecutor:
    """Reusable Gmail API operation executor."""
    
    def __init__(self, gmail_service: Optional["GmailService"] = None):
        self.gmail_service = gmail_service
    
    async def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Gmail operation based on action."""
        if not self.gmail_service:
            raise ValueError("Gmail service not available")
        
        # Store verified gmail_service to avoid repeated None checks
        gmail_service = self.gmail_service
        
        operations = {
            "send": lambda p: self._send_email(gmail_service, p),
            "read": lambda p: self._read_emails(gmail_service, p),
            "search": lambda p: self._search_emails(gmail_service, p),
            "reply": lambda p: self._reply_to_email(gmail_service, p)
        }
        
        operation = operations.get(action)
        if not operation:
            return {"error": f"Unsupported action: {action}"}
        
        return await operation(params)
    
    async def _send_email(self, gmail_service: "GmailService", params: Dict[str, Any]) -> Dict[str, Any]:
        return await gmail_service.send_email(
            to=params["to"],
            subject=params.get("subject", ""),
            body=params.get("body", ""),
            cc=params.get("cc"),
            bcc=params.get("bcc"),
            attachments=params.get("attachments")
        )
    
    async def _read_emails(self, gmail_service: "GmailService", params: Dict[str, Any]) -> Dict[str, Any]:
        messages = await gmail_service.read_emails(
            max_results=params.get("max_results", 10)
        )
        return {"messages": messages}
    
    async def _search_emails(self, gmail_service: "GmailService", params: Dict[str, Any]) -> Dict[str, Any]:
        messages = await gmail_service.search_emails(
            query=params["query"],
            max_results=params.get("max_results", 10)
        )
        return {"messages": messages}
    
    async def _reply_to_email(self, gmail_service: "GmailService", params: Dict[str, Any]) -> Dict[str, Any]:
        return await gmail_service.reply_to_email(
            message_id=params["message_id"],
            body=params.get("reply_body", params.get("body", ""))
        )
