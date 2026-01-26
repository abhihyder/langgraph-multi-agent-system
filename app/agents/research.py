"""
Research Agent - Provides factual, research-based information
Supports optional MCP tool integration for enhanced research capabilities
"""

from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from ..state import AgentState
from ..utils import load_prompt
from ..mcp_client import has_mcp_tools


def research_agent(state: AgentState) -> Dict[str, Any]:
    """
    Research agent that provides factual, analytical information.
    Can optionally use MCP tools for enhanced research capabilities.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with research_output
    """
    user_input = state["user_input"]
    intent = state.get("intent", "")
    
    # Load research prompt
    research_prompt = load_prompt("research.md")
    
    # Check if MCP tools are available
    mcp_available = has_mcp_tools()
    
    if mcp_available:
        # Add tool usage instructions to prompt
        research_prompt += """

**IMPORTANT: External Tools Available**
You have access to external research tools via MCP (Model Context Protocol).
If you need current information, web search, or external data that would improve your answer,
you can request to use these tools. The system will provide the results.

When tools would be helpful, indicate: "I would benefit from using [tool_name] to get [specific information]"
"""
    
    # Initialize LLM
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
    
    # Create messages with context
    tool_status = "✅ MCP tools available" if mcp_available else "📚 Using LLM knowledge only"
    
    messages = [
        SystemMessage(content=research_prompt),
        HumanMessage(content=f"""
Task Intent: {intent}

User Question: {user_input}

Research Mode: {tool_status}

Provide comprehensive research-based information to answer this question.
""")
    ]
    
    # Get research response
    response = llm.invoke(messages)
    
    # Extract content and add tool status note
    output = str(response.content).strip()
    
    if mcp_available:
        output += "\n\n---\n*Note: This response was generated with access to external research tools.*"
    
    # Update only research_output field
    return {
        "research_output": output
    }
