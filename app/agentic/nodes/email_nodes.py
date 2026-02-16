"""
Email Agent - Handles email operations via Gmail API

This agent handles:
- Sending emails
- Reading/fetching emails
- Searching emails  
- Composing emails with AI
- Replying to emails
- Summarizing emails
- Extracting action items from emails

Integrates with:
- GmailService for Gmail API operations
- EmailComposer for AI-powered email composition

Note: Requires OAuth2 credentials to be available in state
"""

from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage

from ..states import AgentState
from ...utils.helpers import load_prompt
from ...utils.llm_factory import get_llm
from ...utils.tracing import trace_agent
from config.llm_config import get_llm_config


@trace_agent("email_agent", run_type="chain", tags=["agent", "email", "integration"])
def email_agent(state: AgentState) -> Dict[str, Any]:
    """
    Email agent that handles Gmail operations.
    
    Capabilities:
    - send_email: Send an email via Gmail
    - read_emails: Fetch emails from inbox
    - search_emails: Search emails with Gmail query syntax
    - compose_email: AI-powered email composition
    - reply_to_email: Reply to an existing email
    - summarize_email: Summarize email content
    - extract_action_items: Extract tasks from email
    
    Args:
        state: Current agent state containing:
            - user_input: User's email-related request
            - email_task: Structured email task with action and parameters
            - gmail_credentials: OAuth2 credentials (optional)
            
    Returns:
        Updated state with email_output
    """
    llm_config = get_llm_config()
    user_input = state["user_input"]
    intent = state.get("intent", "")
    
    # Get email task from state (should be structured by orchestrator)
    email_task = state.get("email_task")
    
    # Load email prompt
    email_prompt = load_prompt("email.md")
    
    # Initialize LLM
    llm = get_llm(
        llm_config.GENERAL_LLM,
        temperature=0.7
    )
    
    # Check if we have gmail credentials
    gmail_credentials = state.get("gmail_credentials")
    
    if not gmail_credentials:
        # Return error if no credentials
        executed = state.get("executed_agents", [])
        return {
            "email_output": "Error: Gmail not authenticated. Please complete OAuth2 flow first via /auth/gmail/login",
            "executed_agents": executed + ["email"]
        }
    
    # If no structured task, parse user input to determine intent
    if not email_task:
        # Use LLM to parse email intent
        parse_messages: List[BaseMessage] = [
            SystemMessage(content=email_prompt),
            HumanMessage(content=f"""Parse this email request and extract the action and parameters:

            User Request: {user_input}

            Intent: {intent}

            Respond with JSON containing:
            - action: One of (send_email, read_emails, search_emails, compose_email, reply_to_email, summarize_email, extract_action_items)
            - parameters: Relevant parameters for the action

            Example:
            {{
                "action": "send_email",
                "parameters": {{
                    "to": ["user@example.com"],
                    "subject": "Meeting request",
                    "body": "Can we meet tomorrow?"
                }}
            }}
            """)
        ]
        
        parse_response = llm.invoke(parse_messages)
        
        # TODO: Parse JSON response and extract email_task
        # For now, create a placeholder response
        output = f"Email agent received request: {user_input}\n\n"
        output += f"Intent analysis: {parse_response.content[:300]}...\n\n"
        output += "Note: Gmail operations require OAuth2 authentication via /auth/gmail/login\n"
        output += "Available actions: send_email, read_emails, search_emails, compose_email, reply_to_email, summarize_email, extract_action_items"
        
        executed = state.get("executed_agents", [])
        return {
            "email_output": output,
            "executed_agents": executed + ["email"]
        }
    
    # Process structured email task
    action = email_task.get("action")
    parameters = email_task.get("parameters", {})
    
    # Route to appropriate handler
    # TODO: Implement actual Gmail API operations via GmailService
    # For now, return placeholder responses
    
    if action == "send_email":
        output = f"Would send email to {parameters.get('to')} with subject: {parameters.get('subject')}"
    elif action == "read_emails":
        output = f"Would read {parameters.get('max_results', 10)} emails from Gmail inbox"
    elif action == "search_emails":
        output = f"Would search emails with Gmail query: {parameters.get('query')}"
    elif action == "compose_email":
        output = f"Would compose email with AI for intent: {parameters.get('intent')}"
    elif action == "reply_to_email":
        output = f"Would reply to message ID: {parameters.get('message_id')}"
    elif action == "summarize_email":
        output = f"Would summarize email ID: {parameters.get('message_id')}"
    elif action == "extract_action_items":
        output = f"Would extract action items from email ID: {parameters.get('message_id')}"
    else:
        output = f"Unknown email action: {action}"
    
    # Update state
    executed = state.get("executed_agents", [])
    return {
        "email_output": output,
        "executed_agents": executed + ["email"]
    }
