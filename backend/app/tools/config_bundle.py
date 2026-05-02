import json
import os
import tempfile
import mlflow
from mlflow import MlflowClient

MODEL_NAME = "agent-config"

DEFAULT_BUNDLE = {
    "classifier_model": "gpt-4o-mini",
    "text_model": "gpt-4o-mini",
    "table_model": "gpt-4o-mini",
    "chart_model": "gpt-4o",
    "synthesis_model": "gpt-4o-mini",
    "judge_model": "gpt-4o-mini",
    "chart_temperature": 0,
    "synthesis_temperature": 0,
    "cache_ttl_days": 30,
    "experiment_tag": "",
    "ab_test": {
        "active": False,
        "challenger_version": None,
        "traffic_split": 0.5,
    },
}


def _register_default_bundle() -> str:
    """Registers DEFAULT_BUNDLE as v1 champion if no model exists yet."""
    client = MlflowClient()

    try:
        client.get_registered_model(MODEL_NAME)
    except Exception:
        client.create_registered_model(
            MODEL_NAME,
            description="Briefed pipeline configuration bundles. Champion alias = current production config.",
        )

    with tempfile.TemporaryDirectory() as tmp:
        config_path = os.path.join(tmp, "config.json")
        with open(config_path, "w") as f:
            json.dump(DEFAULT_BUNDLE, f, indent=2)

        mlflow.set_experiment("briefed-pipeline")
        with mlflow.start_run(run_name="register-default-bundle") as run:
            mlflow.log_artifact(config_path, artifact_path="config")
            run_id = run.info.run_id

        version = client.create_model_version(
            name=MODEL_NAME,
            source=f"runs:/{run_id}/config/config.json",
            run_id=run_id,
            description="Default config bundle — all gpt-4o-mini except chart (gpt-4o vision)",
        )

        client.set_registered_model_alias(MODEL_NAME, "champion", version.version)
        return version.version


def load_champion() -> dict:
    """
    Loads the champion config bundle from MLflow Model Registry.
    Falls back to DEFAULT_BUNDLE if registry is unavailable or empty.
    """
    client = MlflowClient()
    try:
        version = client.get_model_version_by_alias(MODEL_NAME, "champion")
        local_path = mlflow.artifacts.download_artifacts(artifact_uri=version.source)
        with open(local_path) as f:
            bundle = json.load(f)
        bundle["_bundle_version"] = version.version
        return bundle
    except Exception:
        return {**DEFAULT_BUNDLE, "_bundle_version": "default"}


def ensure_champion_exists():
    """Called at startup — registers default bundle if no champion exists."""
    try:
        client = MlflowClient()
        try:
            client.get_model_version_by_alias(MODEL_NAME, "champion")
        except Exception:
            _register_default_bundle()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("MLflow unavailable at startup, skipping champion registration: %s", e)


def get_challenger() -> dict | None:
    """
    Returns the challenger bundle if one is registered, else None.
    Used by the UI indicator logic.
    """
    client = MlflowClient()
    try:
        version = client.get_model_version_by_alias(MODEL_NAME, "challenger")
        local_path = mlflow.artifacts.download_artifacts(artifact_uri=version.source)
        with open(local_path) as f:
            bundle = json.load(f)
        bundle["_bundle_version"] = version.version
        return bundle
    except Exception:
        return None


def register_challenger(
    classifier_model: str, text_model: str, table_model: str,
    chart_model: str, synthesis_model: str, judge_model: str,
    experiment_tag: str,
) -> str:
    """Registers a new challenger bundle and sets the 'challenger' alias."""
    client = MlflowClient()
    champion = load_champion()

    bundle = {
        **champion,
        "classifier_model": classifier_model,
        "text_model": text_model,
        "table_model": table_model,
        "chart_model": chart_model,
        "synthesis_model": synthesis_model,
        "judge_model": judge_model,
        "experiment_tag": experiment_tag,
        "ab_test": {"active": True, "challenger_version": None, "traffic_split": 0.5},
    }
    bundle.pop("_bundle_version", None)

    with tempfile.TemporaryDirectory() as tmp:
        config_path = os.path.join(tmp, "config.json")
        with open(config_path, "w") as f:
            json.dump(bundle, f, indent=2)

        mlflow.set_experiment("briefed-pipeline")
        with mlflow.start_run(run_name="register-challenger") as run:
            mlflow.log_artifact(config_path, artifact_path="config")
            run_id = run.info.run_id

        version = client.create_model_version(
            name=MODEL_NAME,
            source=f"runs:/{run_id}/config/config.json",
            run_id=run_id,
            description=f"Challenger: chart={chart_model}, synthesis={synthesis_model}, split={traffic_split}",
        )
        client.set_registered_model_alias(MODEL_NAME, "challenger", version.version)
        return version.version


def remove_challenger() -> None:
    """Removes the challenger alias, ending the experiment."""
    client = MlflowClient()
    client.delete_registered_model_alias(MODEL_NAME, "challenger")


def promote_challenger() -> str:
    """Promotes the challenger to champion and removes the challenger alias."""
    client = MlflowClient()
    challenger_version = client.get_model_version_by_alias(MODEL_NAME, "challenger")
    client.set_registered_model_alias(MODEL_NAME, "champion", challenger_version.version)
    client.delete_registered_model_alias(MODEL_NAME, "challenger")
    return challenger_version.version
