"""
LangSmith tracing configuration for the gaming support assistant.
"""
import os
from langsmith import traceable

# Default project name if not provided in env vars
DEFAULT_PROJECT_NAME = "gaming-support-assistant"

def setup_langsmith():
    """
    Configure LangSmith tracing for the application.
    
    This function checks if LangSmith environment variables are set
    and provides sensible defaults for local development.
    
    Users should set the following in their .env file:
    - LANGCHAIN_API_KEY: Your LangSmith API key
    - LANGCHAIN_PROJECT: Project name (defaults to "gaming-support-assistant")
    - LANGCHAIN_TRACING_V2: Whether to enable tracing (defaults to "true")
    """
    # Only set defaults if not already set
    if "LANGCHAIN_PROJECT" not in os.environ:
        os.environ["LANGCHAIN_PROJECT"] = DEFAULT_PROJECT_NAME
    
    if "LANGCHAIN_TRACING_V2" not in os.environ:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
    
    # Log configuration
    print(f"LangSmith tracing enabled: {os.environ.get('LANGCHAIN_TRACING_V2', 'false')}")
    print(f"LangSmith project: {os.environ.get('LANGCHAIN_PROJECT', 'Not set')}")
    print(f"LangSmith API key: {'Set' if os.environ.get('LANGCHAIN_API_KEY') else 'Not set'}")
    
    # Warn if API key is missing
    if not os.environ.get("LANGCHAIN_API_KEY"):
        print("WARNING: LANGCHAIN_API_KEY not set. LangSmith tracing will not work.")
        print("Get your API key from https://smith.langchain.com/ and add it to your .env file.")

@traceable
def trace_function(func_name, extra_info=None):
    """
    Decorator for tracing non-LangChain functions.
    
    Args:
        func_name: Name to identify this function in traces
        extra_info: Optional dictionary with additional metadata
        
    Returns:
        Decorated function with LangSmith tracing
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator 