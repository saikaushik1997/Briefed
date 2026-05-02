import logging
import mlflow

logger = logging.getLogger(__name__)
_cache: dict[str, str] = {}


def render_prompt(template: str, **kwargs) -> str:
    """Inject variables into a prompt template using simple string replacement.
    Safer than str.format() — JSON braces in the template are not affected."""
    result = template
    for key, value in kwargs.items():
        result = result.replace(f"{{{key}}}", str(value))
    return result


def load_prompt(name: str, fallback: str) -> str:
    """Load prompt from MLflow registry, cache per process, fall back to hardcoded."""
    if name in _cache:
        return _cache[name]
    try:
        prompt = mlflow.load_prompt(name)
        _cache[name] = prompt.template
        logger.warning("Loaded prompt from MLflow: %s", name)
        return prompt.template
    except Exception as e:
        logger.warning("Falling back to hardcoded prompt for %s: %s", name, e)
        _cache[name] = fallback
        return fallback


def ensure_prompts_exist(prompts: dict[str, tuple[str, str]]) -> None:
    """Register prompts that don't exist yet. Skips if already registered.
    prompts: {name: (template, description)}"""
    for name, (template, description) in prompts.items():
        try:
            mlflow.load_prompt(name)
            logger.warning("Prompt already registered: %s", name)
        except Exception:
            try:
                mlflow.register_prompt(
                    name=name,
                    template=template,
                    commit_message=description,
                    tags={"project": "briefed"},
                )
                logger.warning("Registered prompt: %s", name)
            except Exception as e:
                logger.error("Failed to register prompt %s: %s", name, e)
