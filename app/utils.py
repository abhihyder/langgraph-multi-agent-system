"""
Utility functions for the agentic AI system
"""


def load_prompt(filename: str) -> str:
    """
    Load prompt template from file
    
    Args:
        filename: Name of the prompt file (e.g., 'boss.md')
        
    Returns:
        Content of the prompt file
    """
    with open(f"prompts/{filename}", "r") as f:
        return f.read()
