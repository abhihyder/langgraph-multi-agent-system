"""
Email API Routes

Endpoints for Gmail integration operations:
- Send emails
- Read/fetch emails
- Search emails
- Compose emails with AI
- Reply to emails
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, EmailStr, Field

from app.integrations.email import GmailService, EmailComposer
from config.settings import get_settings


settings = get_settings()
router = APIRouter(prefix="/api/email", tags=["email"])


# ==================== Request/Response Models ====================

class SendEmailRequest(BaseModel):
    """Request model for sending an email"""
    to: List[EmailStr] = Field(..., description="Recipient email addresses")
    subject: str = Field(..., min_length=1, max_length=500, description="Email subject")
    body: str = Field(..., min_length=1, description="Email body content")
    cc: Optional[List[EmailStr]] = Field(default=None, description="CC recipients")
    bcc: Optional[List[EmailStr]] = Field(default=None, description="BCC recipients")
    attachments: Optional[List[str]] = Field(default=None, description="File paths to attach")


class ComposeEmailRequest(BaseModel):
    """Request model for AI-powered email composition"""
    intent: str = Field(..., min_length=1, description="What the email should accomplish")
    recipient_context: Optional[str] = Field(default=None, description="Context about recipient")
    tone: str = Field(default="professional", description="Email tone (professional, formal, casual, etc.)")
    additional_info: Optional[str] = Field(default=None, description="Additional details to include")


class ReplyEmailRequest(BaseModel):
    """Request model for replying to an email"""
    message_id: str = Field(..., description="ID of message to reply to")
    reply_text: Optional[str] = Field(default=None, description="Reply content (if not AI-generated)")
    intent: Optional[str] = Field(default=None, description="Intent for AI-generated reply")
    tone: str = Field(default="professional", description="Reply tone")


class SearchEmailRequest(BaseModel):
    """Request model for searching emails"""
    query: Optional[str] = Field(default=None, description="Gmail search query")
    labels: Optional[List[str]] = Field(default=None, description="Filter by labels")
    max_results: int = Field(default=10, ge=1, le=100, description="Max emails to return")


class EmailResponse(BaseModel):
    """Response model for email operations"""
    success: bool
    message: str
    data: Optional[dict] = None


# ==================== Helper Functions ====================

def get_gmail_service() -> GmailService:
    """
    Get authenticated Gmail service instance.
    TODO: Implement proper OAuth2 flow and credential storage
    """
    # For now, return None - will be implemented in OAuth flow
    # In production, this should retrieve credentials from database/session
    return None


def get_email_composer() -> EmailComposer:
    """Get email composer instance"""
    return EmailComposer()


# ==================== Endpoints ====================

@router.post("/send", response_model=EmailResponse)
async def send_email(
    request: SendEmailRequest,
    gmail_service: GmailService = Depends(get_gmail_service)
):
    """
    Send an email via Gmail.
    
    Requires Gmail authentication via OAuth2.
    """
    if not gmail_service:
        raise HTTPException(
            status_code=401,
            detail="Gmail not authenticated. Please complete OAuth2 flow first."
        )
    
    try:
        result = gmail_service.send_email(
            to=request.to,
            subject=request.subject,
            body=request.body,
            cc=request.cc,
            bcc=request.bcc,
            attachments=request.attachments
        )
        
        return EmailResponse(
            success=True,
            message="Email sent successfully",
            data={"message_id": result["id"], "thread_id": result.get("threadId")}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")


@router.post("/compose", response_model=EmailResponse)
async def compose_email(
    request: ComposeEmailRequest,
    composer: EmailComposer = Depends(get_email_composer)
):
    """
    Compose an email using AI based on intent.
    
    Returns the generated subject and body without sending.
    """
    try:
        result = composer.compose_email(
            intent=request.intent,
            recipient_context=request.recipient_context,
            tone=request.tone,
            additional_info=request.additional_info
        )
        
        return EmailResponse(
            success=True,
            message="Email composed successfully",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compose email: {str(e)}")


@router.get("/read", response_model=EmailResponse)
async def read_emails(
    max_results: int = Query(default=10, ge=1, le=100),
    query: Optional[str] = Query(default=None),
    labels: Optional[List[str]] = Query(default=None),
    gmail_service: GmailService = Depends(get_gmail_service)
):
    """
    Fetch emails from Gmail inbox.
    
    Supports Gmail query syntax (e.g., "is:unread", "from:example@gmail.com").
    """
    if not gmail_service:
        raise HTTPException(
            status_code=401,
            detail="Gmail not authenticated. Please complete OAuth2 flow first."
        )
    
    try:
        emails = gmail_service.read_emails(
            max_results=max_results,
            query=query,
            labels=labels
        )
        
        return EmailResponse(
            success=True,
            message=f"Fetched {len(emails)} emails",
            data={"emails": emails, "count": len(emails)}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read emails: {str(e)}")


@router.post("/search", response_model=EmailResponse)
async def search_emails(
    request: SearchEmailRequest,
    gmail_service: GmailService = Depends(get_gmail_service)
):
    """
    Search emails using Gmail query syntax.
    
    Examples:
    - "is:unread from:boss@company.com"
    - "subject:invoice after:2024/01/01"
    - "has:attachment filename:pdf"
    """
    if not gmail_service:
        raise HTTPException(
            status_code=401,
            detail="Gmail not authenticated. Please complete OAuth2 flow first."
        )
    
    try:
        results = gmail_service.search_emails(
            query=request.query,
            labels=request.labels,
            max_results=request.max_results
        )
        
        return EmailResponse(
            success=True,
            message=f"Found {len(results)} emails",
            data={"emails": results, "count": len(results)}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search emails: {str(e)}")


@router.post("/reply", response_model=EmailResponse)
async def reply_to_email(
    request: ReplyEmailRequest,
    gmail_service: GmailService = Depends(get_gmail_service),
    composer: EmailComposer = Depends(get_email_composer)
):
    """
    Reply to an email.
    
    Can use AI to generate reply based on intent, or send provided reply text.
    """
    if not gmail_service:
        raise HTTPException(
            status_code=401,
            detail="Gmail not authenticated. Please complete OAuth2 flow first."
        )
    
    try:
        # If intent provided, use AI to generate reply
        if request.intent and not request.reply_text:
            # Fetch original email for context
            original_emails = gmail_service.read_emails(max_results=1, query=f"rfc822msgid:{request.message_id}")
            if not original_emails:
                raise HTTPException(status_code=404, detail="Original email not found")
            
            original = original_emails[0]
            
            # Generate reply with AI
            reply_data = composer.compose_reply(
                original_subject=original.get("subject", ""),
                original_body=original.get("body", ""),
                reply_intent=request.intent,
                tone=request.tone
            )
            reply_body = reply_data["body"]
        else:
            reply_body = request.reply_text
        
        if not reply_body:
            raise HTTPException(status_code=400, detail="Either reply_text or intent must be provided")
        
        # Send reply
        result = gmail_service.reply_to_email(
            message_id=request.message_id,
            reply_body=reply_body
        )
        
        return EmailResponse(
            success=True,
            message="Reply sent successfully",
            data={"message_id": result["id"], "thread_id": result.get("threadId")}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send reply: {str(e)}")


@router.get("/user", response_model=EmailResponse)
async def get_user_info(gmail_service: GmailService = Depends(get_gmail_service)):
    """
    Get Gmail user profile information.
    """
    if not gmail_service:
        raise HTTPException(
            status_code=401,
            detail="Gmail not authenticated. Please complete OAuth2 flow first."
        )
    
    try:
        user_info = gmail_service.get_user_info()
        
        return EmailResponse(
            success=True,
            message="User info retrieved",
            data=user_info
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user info: {str(e)}")


@router.post("/summarize", response_model=EmailResponse)
async def summarize_email(
    message_id: str = Query(..., description="Email message ID"),
    gmail_service: GmailService = Depends(get_gmail_service),
    composer: EmailComposer = Depends(get_email_composer)
):
    """
    Summarize an email using AI.
    """
    if not gmail_service:
        raise HTTPException(
            status_code=401,
            detail="Gmail not authenticated. Please complete OAuth2 flow first."
        )
    
    try:
        # Fetch email
        emails = gmail_service.read_emails(max_results=1, query=f"rfc822msgid:{message_id}")
        if not emails:
            raise HTTPException(status_code=404, detail="Email not found")
        
        email = emails[0]
        
        # Summarize
        summary = composer.summarize_email(
            subject=email.get("subject", ""),
            body=email.get("body", "")
        )
        
        return EmailResponse(
            success=True,
            message="Email summarized",
            data={"summary": summary}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to summarize email: {str(e)}")


@router.post("/extract-actions", response_model=EmailResponse)
async def extract_action_items(
    message_id: str = Query(..., description="Email message ID"),
    gmail_service: GmailService = Depends(get_gmail_service),
    composer: EmailComposer = Depends(get_email_composer)
):
    """
    Extract action items from an email using AI.
    """
    if not gmail_service:
        raise HTTPException(
            status_code=401,
            detail="Gmail not authenticated. Please complete OAuth2 flow first."
        )
    
    try:
        # Fetch email
        emails = gmail_service.read_emails(max_results=1, query=f"rfc822msgid:{message_id}")
        if not emails:
            raise HTTPException(status_code=404, detail="Email not found")
        
        email = emails[0]
        
        # Extract action items
        actions = composer.extract_action_items(
            subject=email.get("subject", ""),
            body=email.get("body", "")
        )
        
        return EmailResponse(
            success=True,
            message="Action items extracted",
            data={"action_items": actions}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract action items: {str(e)}")
