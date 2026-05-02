from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..tools.config_bundle import (
    load_champion, get_challenger,
    register_challenger, remove_challenger, promote_challenger,
)

router = APIRouter(prefix="/config", tags=["config"])


class ChallengerRequest(BaseModel):
    classifier_model: str = "gpt-4o-mini"
    text_model: str = "gpt-4o-mini"
    table_model: str = "gpt-4o-mini"
    chart_model: str = "gpt-4o"
    synthesis_model: str = "gpt-4o-mini"
    judge_model: str = "gpt-4o-mini"
    experiment_tag: str = ""


@router.get("/status")
async def get_config_status():
    champion = load_champion()
    challenger = get_challenger()

    def bundle_summary(b):
        return {
            "version": b.get("_bundle_version", "default"),
            "classifier_model": b.get("classifier_model"),
            "text_model": b.get("text_model"),
            "table_model": b.get("table_model"),
            "chart_model": b.get("chart_model"),
            "synthesis_model": b.get("synthesis_model"),
            "judge_model": b.get("judge_model"),
        }

    return {
        "champion": bundle_summary(champion),
        "challenger": bundle_summary(challenger) if challenger else None,
        "experiment_active": challenger is not None,
    }


@router.post("/challenger")
async def create_challenger(body: ChallengerRequest):
    try:
        version = register_challenger(
            classifier_model=body.classifier_model,
            text_model=body.text_model,
            table_model=body.table_model,
            chart_model=body.chart_model,
            synthesis_model=body.synthesis_model,
            judge_model=body.judge_model,
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
