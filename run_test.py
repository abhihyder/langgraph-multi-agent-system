#!/usr/bin/env python3
"""
Quick start script for the Agentic AI System
Run this to test the system quickly
"""

from app import run_agent_system

def test_system():
    """Run quick tests of the agent system"""
    
    print("=" * 70)
    print("AGENTIC AI SYSTEM - QUICK TEST")
    print("=" * 70)
    
    test_cases = [
        {
            "query": "What is Python?",
            "expected_agents": ["research"],
            "description": "Simple research query"
        },
        {
            "query": "Write a short explanation of machine learning",
            "expected_agents": ["research", "writing"],
            "description": "Research + Writing"
        },
        {
            "query": "Create a Python function to calculate fibonacci",
            "expected_agents": ["code"],
            "description": "Code generation"
        }
    ]
    
    print("\n📋 Running Test Cases...\n")
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'─' * 70}")
        print(f"Test {i}: {test['description']}")
        print(f"Query: {test['query']}")
        print(f"Expected Agents: {test['expected_agents']}")
        print(f"{'─' * 70}\n")
        
        try:
            response = run_agent_system(test['query'], verbose=False)
            print(f"✅ Success! Response length: {len(response)} chars")
            print(f"\nPreview: {response[:200]}...")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()
    
    print("\n" + "=" * 70)
    print("Testing Complete!")
    print("=" * 70)
    print("\n💡 To run interactively: python -m app.main")
    print("💡 For verbose output: add --verbose flag in interactive mode\n")


if __name__ == "__main__":
    import os
    
    if not os.getenv("OPENAI_API_KEY"):
        print("\n⚠️  ERROR: OPENAI_API_KEY not found!")
        print("Please set your API key in .env file:")
        print("  1. cp .env.example .env")
        print("  2. Edit .env and add your key")
        print("  3. Run this script again\n")
    else:
        test_system()
