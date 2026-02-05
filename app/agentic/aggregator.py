"""
Aggregator Agent - Synthesizes outputs from specialized agents into final response

The aggregator:
1. Collects outputs from all executed agents
2. Merges them intelligently
3. Removes duplication
4. Creates a coherent final response
"""

from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from .state import AgentState


def aggregator(state: AgentState) -> Dict[str, Any]:
    """
    Aggregates outputs from specialized agents into a final response.
    
    Args:
        state: Current agent state with agent outputs
        
    Returns:
        Updated state with final_output
    """
    user_input = state["user_input"]
    intent = state.get("intent", "")
    
    # Retrieval agent outputs (context/grounding)
    knowledge_output = state.get("knowledge_output")
    memory_output = state.get("memory_output")
    
    # Processing agent outputs (responses)
    general_output = state.get("general_output")
    research_output = state.get("research_output")
    writing_output = state.get("writing_output")
    code_output = state.get("code_output")
    
    # Separate context from responses
    context_parts = []
    response_parts = []
    
    # Add retrieval context (grounding information)
    if knowledge_output:
        context_parts.append(f"## Company Knowledge\n\n{knowledge_output}")
    
    if memory_output:
        context_parts.append(f"## Conversation History\n\n{memory_output}")
    
    # Add agent responses
    if general_output:
        response_parts.append(f"## Response\n\n{general_output}")
    
    if research_output:
        response_parts.append(f"## Research Information\n\n{research_output}")
    
    if writing_output:
        response_parts.append(f"## Content\n\n{writing_output}")
    
    if code_output:
        response_parts.append(f"## Code Implementation\n\n{code_output}")
    
    # If only one response and no context, use it directly
    if len(response_parts) == 1 and not context_parts:
        final_response = response_parts[0].split("\n\n", 1)[1]  # Remove the header
        
        return {
            "final_output": final_response
        }
    
    # If multiple outputs or context exists, aggregate intelligently
    if len(response_parts) > 1 or context_parts:
        # Initialize LLM for aggregation
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.5)
        
        aggregation_prompt = """
You are an Aggregator Agent. Your job is to synthesize context and agent outputs into one coherent final response.

**Input Types:**
- Company Knowledge: Official policies, documentation (use as authoritative grounding)
- Conversation History: User's past discussions (use for personalization)
- Agent Responses: LLM-generated content from specialized agents

**Rules:**
1. Prioritize Company Knowledge when answering policy/procedure questions
2. Use Conversation History to provide personalized, contextual responses
3. Combine all information logically and smoothly
4. Remove any duplication between outputs
5. Maintain accuracy and quality of each contribution
6. Create natural flow: context → research → explanation → code (as applicable)
7. Keep the user's original question in mind
8. Be comprehensive but concise
9. When citing company policies, be explicit (e.g., "According to company policy...")

**Output Format:**
Provide a well-structured, unified response that seamlessly integrates all information.
"""
        
        # Combine everything
        all_content = []
        if context_parts:
            all_content.append("=== CONTEXT ===\n" + "\n\n---\n\n".join(context_parts))
        if response_parts:
            all_content.append("=== AGENT RESPONSES ===\n" + "\n\n---\n\n".join(response_parts))
        
        combined_content = "\n\n==========\n\n".join(all_content)
        
        messages = [
            SystemMessage(content=aggregation_prompt),
            HumanMessage(content=f"""
Original User Question: {user_input}

Intent: {intent}

Content to Synthesize:

{combined_content}

Create a unified, coherent response that answers the user's question.
""")
        ]
        
        response = llm.invoke(messages)
        
        return {
            "final_output": response.content
        }
    
    # Fallback if no outputs (shouldn't happen)
    final_response = "I apologize, but I wasn't able to generate a response. Please try rephrasing your question."
    
    return {
        "final_output": final_response
    }
