"""
Main Entry Point for Agentic AI System

This module provides the interface to interact with the multi-agent system.
"""

import os
from typing import Optional
from dotenv import load_dotenv

from .graph import app
from .state import AgentState


# Load environment variables
load_dotenv()


def run_agent_system(user_input: str, verbose: bool = False) -> str:
    """
    Execute the multi-agent system with a user query.
    
    Args:
        user_input: The user's question or request
        verbose: Whether to print intermediate steps
        
    Returns:
        Final response from the system
    """
    # Initialize state
    initial_state: AgentState = {
        "user_input": user_input,
        "intent": None,
        "research_output": None,
        "writing_output": None,
        "code_output": None,
        "selected_agents": [],
        "final_output": None
    }
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"User Input: {user_input}")
        print(f"{'='*60}\n")
    
    # Execute the graph
    result = app.invoke(initial_state)
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"Intent: {result.get('intent')}")
        print(f"Selected Agents: {result.get('selected_agents')}")
        print(f"{'='*60}\n")
        
        if result.get('research_output'):
            print(f"\n[RESEARCH OUTPUT]")
            print(f"{result['research_output'][:200]}...")
            
        if result.get('writing_output'):
            print(f"\n[WRITING OUTPUT]")
            print(f"{result['writing_output'][:200]}...")
            
        if result.get('code_output'):
            print(f"\n[CODE OUTPUT]")
            print(f"{result['code_output'][:200]}...")
            
        print(f"\n{'='*60}")
        print(f"FINAL OUTPUT:")
        print(f"{'='*60}\n")
    
    return result.get("final_output", "No output generated")


def main():
    """
    Interactive CLI for the agentic AI system.
    """
    print("""
╔════════════════════════════════════════════════════════════╗
║        Multi-Agent AI System with LangGraph                ║
╚════════════════════════════════════════════════════════════╝

Available Agents:
  • Research Agent - Factual information and analysis
  • Writing Agent - Structured content creation
  • Code Agent - Production-quality code generation

Type your question or 'quit' to exit.
""")
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY not found in environment variables.")
        print("Please set your API key in .env file or environment.\n")
        return
    
    while True:
        try:
            user_input = input("\n🤔 Your question: ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!\n")
                break
            
            # Add verbose flag option
            verbose = user_input.endswith(" --verbose")
            if verbose:
                user_input = user_input.replace(" --verbose", "").strip()
            
            print("\n🤖 Processing your request...\n")
            
            response = run_agent_system(user_input, verbose=verbose)
            
            print(f"\n{'─'*60}")
            print(response)
            print(f"{'─'*60}")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please try again.\n")


if __name__ == "__main__":
    main()
