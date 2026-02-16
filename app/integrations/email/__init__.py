"""
Email Integration Package

Gmail service and AI email composition.
"""

from .gmail_service import GmailService
from .email_composer import EmailComposer

__all__ = ["GmailService", "EmailComposer"]
