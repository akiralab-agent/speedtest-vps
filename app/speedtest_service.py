import json
import subprocess
from typing import Any

from pydantic import ValidationError

from app.models import BandwidthResult, PingResult, SpeedtestResult, SpeedtestServer


class SpeedtestCliError(RuntimeError):
    pass


class SpeedtestCliNotFoundError(SpeedtestCliError):
    pass


class SpeedtestTimeoutError(SpeedtestCliError):
    pass


class SpeedtestExecutionError(SpeedtestCliError):
    pass


def _bandwidth_result(payload: dict[str, Any]) -> BandwidthResult:
    bandwidth = int(payload["bandwidth"])
    bits_per_second = bandwidth * 8
    return BandwidthResult(
        bandwidth_bytes_per_second=bandwidth,
        bits_per_second=bits_per_second,
        mbps=round(bits_per_second / 1_000_000, 2),
    )


def _server_result(payload: dict[str, Any] | None) -> SpeedtestServer | None:
    if not payload:
        return None

    server_id = payload.get("id")
    return SpeedtestServer(
        id=int(server_id) if server_id is not None else None,
        name=payload.get("name"),
        location=payload.get("location"),
        country=payload.get("country"),
        host=payload.get("host"),
    )


def parse_speedtest_output(stdout: str) -> SpeedtestResult:
    try:
        data = json.loads(stdout)
        result_data = data.get("result") or {}
        result = SpeedtestResult(
            download=_bandwidth_result(data["download"]),
            upload=_bandwidth_result(data["upload"]),
            ping=PingResult(
                latency_ms=float(data["ping"]["latency"]),
                jitter_ms=data.get("ping", {}).get("jitter"),
            ),
            server=_server_result(data.get("server")),
            isp=data.get("isp"),
            result_url=result_data.get("url"),
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError, ValidationError) as exc:
        raise SpeedtestExecutionError(
            "Nao foi possivel interpretar a saida JSON do Speedtest CLI."
        ) from exc

    return result


def run_speedtest(timeout_seconds: int = 120) -> SpeedtestResult:
    command = ["speedtest", "--accept-license", "--accept-gdpr", "-f", "json"]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            timeout=timeout_seconds,
        )
    except FileNotFoundError as exc:
        raise SpeedtestCliNotFoundError("Binario 'speedtest' nao encontrado.") from exc
    except subprocess.TimeoutExpired as exc:
        raise SpeedtestTimeoutError(
            f"Speedtest CLI excedeu o timeout de {timeout_seconds} segundos."
        ) from exc
    except subprocess.CalledProcessError as exc:
        error_output = (exc.stderr or exc.stdout or "").strip()
        detail = error_output or "Speedtest CLI retornou erro sem detalhes."
        raise SpeedtestExecutionError(detail) from exc

    return parse_speedtest_output(result.stdout)
