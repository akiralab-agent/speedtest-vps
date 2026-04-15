from pydantic import BaseModel, Field


class BandwidthResult(BaseModel):
    bandwidth_bytes_per_second: int = Field(
        description="Valor bruto retornado pelo Speedtest CLI em bytes por segundo."
    )
    bits_per_second: int
    mbps: float


class PingResult(BaseModel):
    latency_ms: float
    jitter_ms: float | None = None


class SpeedtestServer(BaseModel):
    id: int | None = None
    name: str | None = None
    location: str | None = None
    country: str | None = None
    host: str | None = None


class SpeedtestResult(BaseModel):
    download: BandwidthResult
    upload: BandwidthResult
    ping: PingResult
    server: SpeedtestServer | None = None
    isp: str | None = None
    result_url: str | None = None
