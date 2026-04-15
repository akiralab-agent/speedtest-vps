from fastapi import FastAPI, HTTPException, Query

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


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/speedtest", tags=["speedtest"])
def speedtest(
    timeout: int = Query(
        default=120,
        ge=10,
        le=600,
        description="Tempo maximo em segundos para aguardar o Speedtest CLI.",
    ),
):
    try:
        return run_speedtest(timeout_seconds=timeout)
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
