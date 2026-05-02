from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..tools.config_bundle import (
    load_champion, get_challenger,
    register_challenger, remove_challenger, promote_challenger,
)

router = APIRouter(prefix="/config", tags=["config"])


class ChallengerRequest(BaseModel):
    chart_model: str
    synthesis_model: str
    traffic_split: float = 0.3
    experiment_tag: str = ""


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
            "traffic_split": challenger.get("ab_test", {}).get("traffic_split", 0.3),
        } if challenger else None,
        "experiment_active": challenger is not None,
    }


@router.post("/challenger")
async def create_challenger(body: ChallengerRequest):
    try:
        version = register_challenger(
            chart_model=body.chart_model,
            synthesis_model=body.synthesis_model,
            traffic_split=body.traffic_split,
            experiment_tag=body.experiment_tag,
        )
        return {"version": version}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/challenger")
async def end_experiment():
    try:
        remove_challenger()
        return {"status": "experiment ended"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/promote")
async def promote():
    try:
        version = promote_challenger()
        return {"promoted_version": version}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
