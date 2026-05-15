"""
LLM Configuration for Multi-Agent System
Supports Google Gemini, OpenAI, and LM Studio
"""
import os
from langchain_openai import ChatOpenAI
from config import get_config


def get_llm(model_name: str = None, temperature: float = 0.1):
    """
    Returns an LLM instance configured for various providers.
    
    Supports: Google Gemini, OpenCode.ai Zen, OpenAI, LM Studio, Ollama
    
    Args:
        model_name: Optional model name override. If not provided, uses config settings.
        temperature: Temperature for generation (default: 0.1)
    
    Returns:
        Configured LLM instance
    """
    config = get_config()
    
    # If no model name provided, determine from config (priority order)
    if not model_name:
        if config.anthropic_api_key:
            model_name = config.anthropic_model
        elif config.gemini_enabled:
            model_name = config.gemini_model
        elif config.opencode_enabled:
            model_name = config.opencode_model
        elif config.lm_studio_enabled:
            model_name = config.lm_studio_model
        elif config.openai_enabled:
            model_name = "gpt-4"
        elif config.ollama_enabled:
            model_name = config.ollama_model
        else:
            model_name = "gpt-3.5-turbo"  # fallback
    
    # Check if using Anthropic (or OpenCode Zen Anthropic-Compatible)
    if config.anthropic_api_key and (model_name == config.anthropic_model or "claude" in model_name.lower() or "minimax-m" in model_name.lower()):
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=model_name,
            temperature=temperature,
            api_key=config.anthropic_api_key,
            base_url=config.anthropic_base_url
        )

    # Check if Gemini model
    if "gemini" in model_name.lower():
        # Ensure model name doesn't have redundant 'models/' prefix
        clean_model = model_name.replace("models/", "")
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            google_api_key = os.getenv("GOOGLE_API_KEY")
            if not google_api_key:
                raise ValueError("GOOGLE_API_KEY not set for Gemini model")
            return ChatGoogleGenerativeAI(
                model=clean_model,
                temperature=temperature,
                google_api_key=google_api_key
            )
        except ImportError:
            # Fallback to OpenAI-compatible endpoint if package not installed
            google_api_key = os.getenv("GOOGLE_API_KEY")
            if not google_api_key:
                raise ValueError("GOOGLE_API_KEY not set for Gemini model")
            return ChatOpenAI(
                model=model_name,
                temperature=temperature,
                api_key=google_api_key,
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
            )
    
    # Check if using OpenCode.ai Zen
    elif "zen" in model_name.lower() or config.opencode_enabled:
        if not config.opencode_api_key:
            raise ValueError("OPENCODE_API_KEY not set for OpenCode.ai Zen")
        return ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=config.opencode_api_key,
            base_url=config.opencode_base_url
        )
    
    # Check if using LM Studio
    elif config.lm_studio_enabled:
        return ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=os.getenv("OPENAI_API_KEY", "lm-studio"),
            base_url=config.lm_studio_host + "/v1"
        )
    
    # Check if using Ollama
    elif config.ollama_enabled:
        return ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key="ollama",
            base_url=config.ollama_host + "/v1"
        )
    
    # Default to OpenAI
    else:
        if not config.openai_api_key:
            raise ValueError("OPENAI_API_KEY not set and no other LLM provider enabled")
        return ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=config.openai_api_key
        )

# Made with Bob
