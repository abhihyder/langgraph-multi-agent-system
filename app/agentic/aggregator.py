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
    research_output = state.get("research_output")
    writing_output = state.get("writing_output")
    code_output = state.get("code_output")
    
    # Collect available outputs
    outputs = []
    
    if research_output:
        outputs.append(f"## Research Information\n\n{research_output}")
    
    if writing_output:
        outputs.append(f"## Content\n\n{writing_output}")
    
    if code_output:
        outputs.append(f"## Code Implementation\n\n{code_output}")
    
    # If only one output, use it directly
    if len(outputs) == 1:
        return {
            "final_output": outputs[0].split("\n\n", 1)[1]  # Remove the header
        }
    
    # If multiple outputs, aggregate them intelligently
    if len(outputs) > 1:
        # Initialize LLM for aggregation
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.5)
        
        aggregation_prompt = """
You are an Aggregator Agent. Your job is to synthesize multiple agent outputs into one coherent, well-structured final response.

**Rules:**
1. Combine the information logically and smoothly
2. Remove any duplication between outputs
3. Maintain the quality and accuracy of each agent's contribution
4. Create a natural flow from research → explanation → code (as applicable)
5. Keep the user's original question in mind
6. Be comprehensive but concise

**Output Format:**
Provide a well-structured, unified response that seamlessly integrates all the information.
"""
        
        combined_outputs = "\n\n---\n\n".join(outputs)
        
        messages = [
            SystemMessage(content=aggregation_prompt),
            HumanMessage(content=f"""
Original User Question: {user_input}

Intent: {intent}

Agent Outputs to Synthesize:

{combined_outputs}

Create a unified, coherent response that answers the user's question.
""")
        ]
        
        response = llm.invoke(messages)
        
        return {
            "final_output": response.content
        }
    
    # Fallback if no outputs (shouldn't happen)
    return {
        "final_output": "I apologize, but I wasn't able to generate a response. Please try rephrasing your question."
    }
