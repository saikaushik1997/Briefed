from fastapi import APIRouter
from ..tools.config_bundle import load_champion, get_challenger

router = APIRouter(prefix="/config", tags=["config"])


@router.get("/status")
async def get_config_status():
    champion = load_champion()
    challenger = get_challenger()

    return {
        "champion": {
            "version": champion.get("_bundle_version", "default"),
            "chart_model": champion.get("chart_model"),
            "synthesis_model": champion.get("synthesis_model"),
            "ab_test": champion.get("ab_test", {}),
        },
        "challenger": {
            "version": challenger.get("_bundle_version"),
            "chart_model": challenger.get("chart_model"),
            "synthesis_model": challenger.get("synthesis_model"),
            "traffic_split": champion.get("ab_test", {}).get("traffic_split", 0.5),
        } if challenger else None,
        "experiment_active": champion.get("ab_test", {}).get("active", False),
    }
