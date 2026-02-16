"""
Email Agent Graph - LangGraph implementation of email agent

This is the graph-based implementation of the email agent, replacing the
simple function-based email_agent. Uses StateGraph with multiple nodes for:
- Intent parsing (LLM)
- Parameter validation (Processing)
- Action routing (Router)
- Email composition (LLM)
- Gmail API calls (Tool)
- Response formatting (Processing)
- Error handling (Processing)

Architecture:
    user_input → parse_intent → validate_params → route_action
                                                       ↓
                     format_response ← gmail_api ← compose_email (if needed)
                          ↓
                        END / error_handler

Integration:
- GmailService for Gmail API operations
- EmailComposer for AI-powered email composition
- OAuth2 credentials from state
"""

from typing import Dict, Any, Optional, List, TypedDict
import json
import asyncio

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage

from .base_graph import BaseAgentGraph, log_node_execution, retry_on_failure, NodeType
from ..states import EmailState
from ...exceptions import EmailServiceError, ParameterValidationError, NotAuthenticatedError
from ...integrations.email.gmail_service import GmailService
from ...integrations.email.email_composer import EmailComposer
from ...utils.helpers import load_prompt
from ...utils.llm_factory import get_llm
from ...utils.email_utils import (
    EmailValidator, GmailOperationExecutor, parse_llm_json_response,
    format_error_message, format_gmail_list_response
)
from config.llm_config import get_llm_config
import logging


logger = logging.getLogger(__name__)


class EmailAgentGraph(BaseAgentGraph):
    """
    Email Agent as a LangGraph sub-graph.
    
    Handles all email-related operations via Gmail API with AI assistance.
    
    Nodes:
    1. parse_intent (LLM) - Parse user request into structured action
    2. validate_params (Processing) - Validate email addresses and parameters
    3. route_action (Router) - Route to appropriate handler based on action
    4. compose_email (LLM) - AI-powered email composition (for send/reply)
    5. gmail_api (Tool) - Execute Gmail API operation
    6. format_response (Processing) - Format result for orchestrator
    7. error_handler (Processing) - Handle errors gracefully
    
    Example:
        gmail_service = GmailService(credentials)
        email_composer = EmailComposer()
        
        graph = EmailAgentGraph(gmail_service, email_composer)
        result = graph.invoke({"user_input": "Send email to john@example.com about meeting"})
    """
    
    def __init__(self, gmail_service: Optional[GmailService] = None, email_composer: Optional[EmailComposer] = None):
        super().__init__()
        self.gmail_service = gmail_service
        self.email_composer = email_composer
        self.llm_config = get_llm_config()
        # Reusable components
        self.validator = EmailValidator()
        self.executor = GmailOperationExecutor(gmail_service)
        self.graph = self.build_graph()
    
    def _get_gmail_service(self, credentials: Optional[Dict[str, Any]] = None) -> Optional[GmailService]:
        """
        Get or create GmailService instance.
        
        Args:
            credentials: OAuth2 credentials
            
        Returns:
            GmailService instance or None if no credentials
        """
        if self.gmail_service:
            return self.gmail_service
        
        if credentials:
            # Create GmailService with credentials
            self.gmail_service = GmailService(config=credentials)
            return self.gmail_service
        
        return None
    
    def build_graph(self):
        """Build the email agent graph with all nodes and edges"""
        logger.info("Building EmailAgentGraph")
        
        # Create StateGraph
        graph = StateGraph(EmailState)
        
        # Add nodes
        graph.add_node("parse_intent", self.parse_intent_node)
        graph.add_node("validate_params", self.validate_params_node)
        graph.add_node("compose_email", self.compose_email_node)
        graph.add_node("gmail_api", self.gmail_api_node)
        graph.add_node("format_response", self.format_response_node)
        graph.add_node("error_handler", self.error_handler_node)
        
        # Add edges
        graph.add_edge("parse_intent", "validate_params")
        
        # Conditional: After validation, check if composition needed
        graph.add_conditional_edges(
            "validate_params",
            self.should_compose_email,
            {
                "compose": "compose_email",
                "direct_api": "gmail_api",
                "error": "error_handler"
            }
        )
        
        graph.add_edge("compose_email", "gmail_api")
        
        # Conditional: After Gmail API, check for errors
        graph.add_conditional_edges(
            "gmail_api",
            self.check_for_errors,
            {
                "success": "format_response",
                "error": "error_handler"
            }
        )
        
        graph.add_edge("format_response", END)
        graph.add_edge("error_handler", END)
        
        # Set entry point
        graph.set_entry_point("parse_intent")
        
        logger.info("EmailAgentGraph built successfully")
        return graph.compile()
    
    # ========== NODE IMPLEMENTATIONS ==========
    
    @log_node_execution(NodeType.LLM)
    @retry_on_failure(max_retries=2)
    def parse_intent_node(self, state: EmailState) -> EmailState:
        """
        LLM Node: Parse user request into structured email action.
        
        Extracts:
        - action: send, read, search, compose, reply, summarize, extract_actions
        - parameters: Action-specific parameters (to, subject, body, query, etc.)
        """
        logger.info("Parsing email intent from user input")
        
        user_input = state.get("user_input", "")
        intent = state.get("intent", "")
        
        # Load email prompt
        email_prompt = load_prompt("email.md")
        
        # Initialize LLM (use GPT-4 for accurate intent parsing)
        llm = get_llm(self.llm_config.GENERAL_LLM, temperature=0.3)
        
        # Construct parsing prompt
        messages = [
            SystemMessage(content=email_prompt),
            HumanMessage(content=f"""Parse this email request and extract the action and parameters.

            User Request: {user_input}
            Intent: {intent}

            Respond with JSON containing:
            - action: One of (send, read, search, compose, reply, summarize, extract_actions)
            - parameters: Relevant parameters for the action

            For "send" action:
            - to: list of email addresses
            - subject: email subject
            - body: email body (if provided)

            For "read" action:
            - max_results: number of emails to read (default 10)

            For "search" action:
            - query: Gmail search query

            For "compose" action:
            - intent: what the email should be about
            - tone: professional/casual/formal/etc.

            For "reply" action:
            - message_id: ID of message to reply to
            - reply_body: reply content

            For "summarize" or "extract_actions":
            - message_id: ID of message

            Example response:
            {{
            "action": "send",
            "parameters": {{
                "to": ["user@example.com"],
                "subject": "Meeting request",
                "body": "Can we meet tomorrow?"
            }}
            }}

            Respond with ONLY the JSON, no other text.""")
        ]
        
        response = llm.invoke(messages)
        content = str(response.content).strip() if response.content else ""
        
        # Parse JSON using reusable utility
        try:
            parsed = parse_llm_json_response(content)
            action = parsed.get("action", "send")
            parameters = parsed.get("parameters", {})
            
            logger.info(f"Parsed intent: action={action}, params={list(parameters.keys())}")
            
            state["action"] = action
            state["email_params"] = parameters
            state["parsed_intent"] = parsed
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response content: {content}")
            state["error"] = f"Failed to parse email intent: {str(e)}"
            state["error_type"] = "IntentParsingError"
        
        return state
    
    @log_node_execution(NodeType.PROCESSING)
    def validate_params_node(self, state: EmailState) -> EmailState:
        """
        Processing Node: Validate email parameters.
        
        Checks:
        - Email addresses are valid
        - Required parameters present
        - Gmail credentials available
        """
        logger.info("Validating email parameters")
        
        action = state.get("action", "")
        params = state.get("email_params", {})
        
        # Check for Gmail credentials
        if not state.get("gmail_credentials"):
            logger.warning("Gmail credentials not found in state")
            state["error"] = "Gmail not authenticated. Please complete OAuth2 flow first."
            state["error_type"] = "AuthenticationError"
            return state
        
        # Validate based on action
        validation_error = self.validator.validate_by_action(action, params)
        if validation_error:
            state["error"] = validation_error
            state["error_type"] = "ValidationError"
            return state
        
        # Mark as validated
        state["validated"] = True
        logger.info("Parameters validated successfully")
        
        return state
    
    def should_compose_email(self, state: EmailState) -> str:
        """
        Router: Determine if email composition is needed.
        
        Returns:
        - "compose": Need to compose email content
        - "direct_api": Can call Gmail API directly
        - "error": Validation failed
        """
        if state.get("error"):
            return "error"
        
        action = state.get("action", "")
        params = state.get("email_params", {})
        
        # Composition needed for send/reply if no body provided
        if action == "send" and not params.get("body"):
            logger.info("Email composition needed (no body provided)")
            return "compose"
        
        if action == "reply" and not params.get("reply_body"):
            logger.info("Reply composition needed (no reply_body provided)")
            return "compose"
        
        if action == "compose":
            logger.info("Explicit composition requested")
            return "compose"
        
        # For other actions, go directly to API
        logger.info(f"Direct API call for action: {action}")
        return "direct_api"
    
    @log_node_execution(NodeType.LLM)
    @retry_on_failure(max_retries=2)
    def compose_email_node(self, state: EmailState) -> EmailState:
        """
        LLM Node: Compose email content using AI.
        
        Uses EmailComposer or direct LLM for generating email content.
        """
        logger.info("Composing email content with AI")
        
        action = state.get("action", "")
        params = state.get("email_params", {})
        user_input = state.get("user_input", "")
        
        try:
            if self.email_composer and action == "send":
                # Use EmailComposer for sophisticated composition
                tone = params.get("tone", "professional")
                intent = params.get("intent", user_input)
                
                # EmailComposer.compose_email is async
                import asyncio
                email_content = asyncio.run(self.email_composer.compose_email(
                    intent=intent,
                    tone=tone
                ))
                
                # Update parameters with composed content
                params["body"] = email_content
                if not params.get("subject"):
                    # Extract subject from composed email or use intent
                    params["subject"] = intent[:50] if len(intent) > 50 else intent
                
                state["email_content"] = {"body": email_content, "subject": params["subject"]}
                state["email_params"] = params
                
                logger.info(f"Email composed: subject='{params['subject']}', body length={len(params['body'])}")
            
            else:
                # Simple LLM-based composition
                llm = get_llm(self.llm_config.GENERAL_LLM, temperature=0.7)
                
                prompt = f"Compose a {params.get('tone', 'professional')} email based on: {user_input}"
                response = llm.invoke([HumanMessage(content=prompt)])
                
                params["body"] = response.content
                state["email_params"] = params
                state["email_content"] = {"body": response.content}
                
                logger.info(f"Email composed with LLM: {len(response.content)} chars")
        
        except Exception as e:
            logger.error(f"Email composition failed: {str(e)}")
            state["error"] = f"Failed to compose email: {str(e)}"
            state["error_type"] = "CompositionError"
        
        return state
    
    @log_node_execution(NodeType.TOOL)
    @retry_on_failure(max_retries=2)
    def gmail_api_node(self, state: EmailState) -> EmailState:
        """
        Tool Node: Execute Gmail API operation.
        
        Calls appropriate GmailService method based on action.
        """
        logger.info("Executing Gmail API operation")
        
        action = state.get("action", "")
        params = state.get("email_params", {})
        credentials = state.get("gmail_credentials")
        
        try:
            # Get or create GmailService
            gmail_service = self._get_gmail_service(credentials)
            
            if not gmail_service:
                raise ValueError("Gmail service not available - no credentials provided")
            
            # Authenticate if needed
            if not gmail_service.is_authenticated and credentials:
                import asyncio
                # Note: authenticate is async, we need to run it
                asyncio.run(gmail_service.authenticate(credentials))
            
            # Route to appropriate Gmail API method (these are async methods)
            import asyncio
            
            if action == "send":
                result = asyncio.run(gmail_service.send_email(
                    to=params["to"],
                    subject=params.get("subject", ""),
                    body=params.get("body", ""),
                    cc=params.get("cc"),
                    bcc=params.get("bcc"),
                    attachments=params.get("attachments")
                ))
            
            elif action == "read":
                result = asyncio.run(gmail_service.read_emails(
                    max_results=params.get("max_results", 10)
                ))
            
            elif action == "search":
                result = asyncio.run(gmail_service.search_emails(
                    query=params["query"],
                    max_results=params.get("max_results", 10)
                ))
            
            elif action == "reply":
                result = asyncio.run(gmail_service.reply_to_email(
                    message_id=params["message_id"],
                    body=params.get("reply_body", params.get("body", ""))
                ))
            
            else:
                result = {"error": f"Unsupported action: {action}"}
            
            # Normalize result to dict (some methods return lists)
            if isinstance(result, list):
                state["gmail_response"] = {"messages": result}
            else:
                state["gmail_response"] = result
            logger.info(f"Gmail API operation '{action}' completed successfully")
        
        except Exception as e:
            logger.error(f"Gmail API operation failed: {str(e)}")
            state["error"] = f"Gmail API error: {str(e)}"
            state["error_type"] = "GmailAPIError"
            state["gmail_response"] = {"error": str(e)}
        
        return state
    
    def check_for_errors(self, state: EmailState) -> str:
        """
        Router: Check if Gmail API call had errors.
        
        Returns:
        - "success": Operation succeeded
        - "error": Operation failed
        """
        if state.get("error"):
            return "error"
        
        gmail_response = state.get("gmail_response") or {}
        if gmail_response.get("error"):
            state["error"] = gmail_response["error"]
            state["error_type"] = "GmailAPIError"
            return "error"
        
        return "success"
    
    @log_node_execution(NodeType.PROCESSING)
    def format_response_node(self, state: EmailState) -> EmailState:
        """
        Processing Node: Format result for orchestrator.
        
        Creates human-readable output from Gmail API response.
        """
        logger.info("Formatting email agent response")
        
        action = state.get("action", "")
        gmail_response = state.get("gmail_response") or {}
        
        try:
            output = ""
            
            if action == "send":
                message_id = gmail_response.get("id", "unknown")
                output = f"✅ Email sent successfully! Message ID: {message_id}"
            
            elif action == "read":
                messages = gmail_response.get("messages", [])
                output = f"📧 Retrieved {len(messages)} emails:\n\n"
                for msg in messages[:5]:  # Show first 5
                    output += f"- From: {msg.get('from', 'Unknown')}\n"
                    output += f"  Subject: {msg.get('subject', 'No subject')}\n"
                    output += f"  Date: {msg.get('date', 'Unknown')}\n\n"
                
                if len(messages) > 5:
                    output += f"... and {len(messages) - 5} more emails\n"
            
            elif action == "search":
                messages = gmail_response.get("messages", [])
                output = f"🔍 Found {len(messages)} matching emails:\n\n"
                for msg in messages[:5]:
                    output += f"- {msg.get('subject', 'No subject')} (from {msg.get('from', 'Unknown')})\n"
                
                if len(messages) > 5:
                    output += f"... and {len(messages) - 5} more results\n"
            
            elif action == "reply":
                message_id = gmail_response.get("id", "unknown")
                output = f"✅ Reply sent successfully! Message ID: {message_id}"
            
            else:
                output = f"Email action '{action}' completed."
            
            state["email_output"] = output
            state["formatted_result"] = {
                "success": True,
                "output": output,
                "action": action,
                "gmail_response": gmail_response
            }
            
            logger.info("Response formatted successfully")
        
        except Exception as e:
            logger.error(f"Response formatting failed: {str(e)}")
            state["error"] = f"Failed to format response: {str(e)}"
            state["error_type"] = "FormattingError"
        
        return state
    
    @log_node_execution(NodeType.PROCESSING)
    def error_handler_node(self, state: EmailState) -> EmailState:
        """
        Processing Node: Handle errors gracefully.
        
        Formats error response for user.
        """
        logger.info("Handling email agent error")
        
        error_msg = state.get("error", "Unknown error occurred")
        error_type = state.get("error_type", "Error")
        action = state.get("action", "unknown")
        
        output = f"❌ Email operation failed:\n\n"
        output += f"Error Type: {error_type}\n"
        output += f"Action: {action}\n"
        output += f"Details: {error_msg}\n\n"
        
        # Add helpful hints based on error type
        if error_type == "AuthenticationError":
            output += "💡 Tip: Complete Gmail OAuth2 flow at /auth/gmail/login"
        elif error_type == "ValidationError":
            output += "💡 Tip: Check that all required parameters are provided and valid"
        elif error_type == "GmailAPIError":
            output += "💡 Tip: Check Gmail API quota and credentials"
        
        state["email_output"] = output
        state["formatted_result"] = {
            "success": False,
            "error": error_msg,
            "error_type": error_type,
            "action": action
        }
        
        return state


# Factory function for creating email agent graph
def create_email_agent_graph(credentials: Optional[Dict[str, Any]] = None) -> EmailAgentGraph:
    """
    Factory function to create email agent graph.
    
    Args:
        credentials: Optional Gmail OAuth2 credentials
        
    Returns:
        EmailAgentGraph instance
    """
    gmail_service = None
    if credentials:
        gmail_service = GmailService(config=credentials)
    
    email_composer = EmailComposer()
    
    return EmailAgentGraph(
        gmail_service=gmail_service,
        email_composer=email_composer
    )
