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


def extract_usage(response) -> dict:
    """
    Pulls token counts from a LangChain AIMessage response.
    LangChain standardised on usage_metadata in recent versions but
    some models still return via response_metadata — check both.
    Returns {"input_tokens": int, "output_tokens": int}.
    """
    # Preferred: usage_metadata (LangChain standard)
    if hasattr(response, "usage_metadata") and response.usage_metadata:
        m = response.usage_metadata
        return {
            "input_tokens": m.get("input_tokens", 0),
            "output_tokens": m.get("output_tokens", 0),
        }
    # Fallback: response_metadata.token_usage (OpenAI style)
    token_usage = (getattr(response, "response_metadata", {}) or {}).get("token_usage", {})
    return {
        "input_tokens": token_usage.get("prompt_tokens", 0),
        "output_tokens": token_usage.get("completion_tokens", 0),
    }
