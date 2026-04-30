import os
import litellm
from langsmith import traceable
from langchain_community.chat_models import ChatLiteLLM
from ..config import settings


def setup():
    """
    Push API keys into env so both LiteLLM and LangChain wrappers pick them up.
    LangSmith tracing is propagated automatically by LangChain — no manual
    callback needed. All LLM calls nest under the LangGraph trace.
    """
    os.environ["OPENAI_API_KEY"] = settings.openai_api_key
    os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key

    if settings.langsmith_api_key:
        os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
        os.environ["LANGCHAIN_TRACING_V2"] = settings.langchain_tracing_v2
        os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project


def get_model(model_name: str, temperature: float = 0, max_tokens: int = 1024) -> ChatLiteLLM:
    """
    Returns a LangChain-compatible LiteLLM model.
    Using ChatLiteLLM (not raw litellm.acompletion) ensures LangSmith context
    from LangGraph propagates — all LLM calls appear as children of the pipeline trace.
    Model name is the same LiteLLM string: "gpt-4o-mini", "claude-3-5-sonnet-20241022", etc.
    """
    return ChatLiteLLM(model=model_name, temperature=temperature, max_tokens=max_tokens)


def agent_trace(name: str):
    """
    Wraps an agent's run() as a named LangSmith span.
    Usage: @agent_trace("classifier")
    """
    return traceable(name=name, run_type="chain")
