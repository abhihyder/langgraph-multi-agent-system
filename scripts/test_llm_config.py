"""
Test script to validate LLM provider configuration
Run this to ensure your LLM factory is working correctly
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.llm_factory import LLMFactory, get_llm
from config.llm_config import get_llm_config


def test_configuration():
    """Test LLM configuration and provider availability"""
    
    llm_config = get_llm_config()
    
    print("=" * 60)
    print("LLM Provider Configuration Test")
    print("=" * 60)
    print()
    
    # Check available providers
    print("📋 Supported Providers:")
    providers = LLMFactory.get_available_providers()
    for provider, config in providers.items():
        print(f"  • {provider}: {', '.join(config['models'][:3])}...")
    print()
    
    # Check API keys
    print("🔑 API Keys Status:")
    print(f"  • OpenAI:    {'✅ Set' if llm_config.OPENAI_API_KEY else '❌ Missing'}")
    print(f"  • Anthropic: {'✅ Set' if llm_config.ANTHROPIC_API_KEY else '❌ Missing'}")
    print(f"  • Google:    {'✅ Set' if llm_config.GOOGLE_API_KEY else '❌ Missing'}")
    print()
    
    # Check agent configurations
    print("🤖 Agent LLM Configuration:")
    agent_configs = {
        "Orchestrator": llm_config.ORCHESTRATOR_LLM,
        "Research": llm_config.RESEARCH_LLM,
        "Writing": llm_config.WRITING_LLM,
        "Code": llm_config.CODE_LLM,
        "General": llm_config.GENERAL_LLM,
        "Aggregator": llm_config.AGGREGATOR_LLM,
    }
    
    for agent, config in agent_configs.items():
        provider, model = LLMFactory._parse_llm_config(config)
        is_valid = LLMFactory._validate_provider_model(provider, model)
        status = "✅" if is_valid else "⚠️"
        print(f"  {status} {agent:12} → {provider}:{model}")
    print()
    
    # Check temperature settings
    print("🌡️  Temperature Settings:")
    print(f"  • Orchestrator: {llm_config.ORCHESTRATOR_TEMPERATURE}")
    print(f"  • Research:     {llm_config.RESEARCH_TEMPERATURE}")
    print(f"  • Writing:      {llm_config.WRITING_TEMPERATURE}")
    print(f"  • Code:         {llm_config.CODE_TEMPERATURE}")
    print(f"  • Aggregator:   {llm_config.AGGREGATOR_TEMPERATURE}")
    print()
    
    # Test LLM creation for agents with available API keys
    print("🧪 Testing LLM Creation:")
    test_results = []
    
    for agent, config in agent_configs.items():
        try:
            provider, model = LLMFactory._parse_llm_config(config)
            
            # Check if API key is available for this provider
            if provider == "openai" and not llm_config.OPENAI_API_KEY:
                test_results.append((agent, config, "⚠️", "OpenAI API key missing"))
                continue
            elif provider == "anthropic" and not llm_config.ANTHROPIC_API_KEY:
                test_results.append((agent, config, "⚠️", "Anthropic API key missing"))
                continue
            elif provider == "google" and not llm_config.GOOGLE_API_KEY:
                test_results.append((agent, config, "⚠️", "Google API key missing"))
                continue
            
            # Try to create LLM instance
            llm = get_llm(config, temperature=0.5)
            test_results.append((agent, config, "✅", f"Created {provider}:{model}"))
        except Exception as e:
            test_results.append((agent, config, "❌", str(e)[:50]))
    
    for agent, config, status, message in test_results:
        print(f"  {status} {agent:12} → {message}")
    print()
    
    # Summary
    success_count = sum(1 for _, _, status, _ in test_results if status == "✅")
    warning_count = sum(1 for _, _, status, _ in test_results if status == "⚠️")
    error_count = sum(1 for _, _, status, _ in test_results if status == "❌")
    
    print("=" * 60)
    print(f"Summary: {success_count} ✅  {warning_count} ⚠️  {error_count} ❌")
    print("=" * 60)
    print()
    
    if error_count > 0:
        print("❌ Some LLM configurations failed. Check the errors above.")
        return False
    elif warning_count > 0:
        print("⚠️  Some providers need API keys. Add them to .env to use those providers.")
        return True
    else:
        print("✅ All LLM configurations are valid!")
        return True


def test_simple_inference():
    """Test a simple inference with available provider"""
    llm_config = get_llm_config()
    
    print("=" * 60)
    print("Simple Inference Test")
    print("=" * 60)
    print()
    
    # Find first available provider
    available_provider = None
    if llm_config.OPENAI_API_KEY:
        available_provider = "openai:gpt-4o-mini"
    elif llm_config.ANTHROPIC_API_KEY:
        available_provider = "anthropic:claude-3-5-haiku-20241022"
    elif llm_config.GOOGLE_API_KEY:
        available_provider = "google:gemini-1.5-flash"
    
    if not available_provider:
        print("❌ No API keys configured. Add at least one provider API key to .env")
        return False
    
    print(f"Testing with: {available_provider}")
    print()
    
    try:
        llm = get_llm(available_provider, temperature=0.7)
        response = llm.invoke("Say 'Hello from the multi-agent system!' in one sentence.")
        print(f"Response: {response.content}")
        print()
        print("✅ Inference successful!")
        return True
    except Exception as e:
        print(f"❌ Inference failed: {e}")
        return False


if __name__ == "__main__":
    print()
    
    # Test configuration
    config_ok = test_configuration()
    
    if config_ok:
        print()
        # Test simple inference
        test_simple_inference()
    
    print()
