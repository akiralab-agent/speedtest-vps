from fastapi import FastAPI, HTTPException, Query

from app.database import init_database, list_speedtest_points, save_speedtest_result
from app.models import SpeedtestRecord, SpeedtestTimeSeriesResponse
from app.speedtest_service import (
    SpeedtestCliError,
    SpeedtestCliNotFoundError,
    SpeedtestExecutionError,
    SpeedtestTimeoutError,
    run_speedtest,
)

app = FastAPI(
    title="Speedtest VPS API",
    description="API para medir a velocidade de conexao do servidor via Ookla Speedtest CLI.",
    version="0.1.0",
)


@app.on_event("startup")
def startup() -> None:
    init_database()


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/speedtest", response_model=SpeedtestRecord, tags=["speedtest"])
def speedtest(
    timeout: int = Query(
        default=120,
        ge=10,
        le=600,
        description="Tempo maximo em segundos para aguardar o Speedtest CLI.",
    ),
) -> SpeedtestRecord:
    try:
        result = run_speedtest(timeout_seconds=timeout)
        return save_speedtest_result(result)
    except SpeedtestCliNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Ookla Speedtest CLI nao encontrado. Instale o binario 'speedtest' "
                "no servidor e confirme que ele esta disponivel no PATH."
            ),
        ) from exc
    except SpeedtestTimeoutError as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except SpeedtestExecutionError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except SpeedtestCliError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get(
    "/speedtest/history",
    response_model=SpeedtestTimeSeriesResponse,
    tags=["speedtest"],
)
def speedtest_history(
    limit: int = Query(
        default=100,
        ge=1,
        le=5000,
        description="Quantidade maxima de medicoes retornadas em ordem cronologica.",
    ),
) -> SpeedtestTimeSeriesResponse:
    points = list_speedtest_points(limit=limit)
    return SpeedtestTimeSeriesResponse(count=len(points), points=points)
