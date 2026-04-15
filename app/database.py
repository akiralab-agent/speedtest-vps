import os
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.models import SpeedtestRecord, SpeedtestResult, SpeedtestTimeSeriesPoint

DEFAULT_DATABASE_PATH = "speedtest_results.sqlite3"
DATABASE_PATH = Path(os.getenv("SPEEDTEST_DB_PATH", DEFAULT_DATABASE_PATH))


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_database() -> None:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS speedtest_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                download_bandwidth_bytes_per_second INTEGER NOT NULL,
                download_bits_per_second INTEGER NOT NULL,
                download_mbps REAL NOT NULL,
                upload_bandwidth_bytes_per_second INTEGER NOT NULL,
                upload_bits_per_second INTEGER NOT NULL,
                upload_mbps REAL NOT NULL,
                ping_latency_ms REAL NOT NULL,
                ping_jitter_ms REAL,
                server_id INTEGER,
                server_name TEXT,
                server_location TEXT,
                server_country TEXT,
                server_host TEXT,
                isp TEXT,
                result_url TEXT
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_speedtest_results_created_at
            ON speedtest_results (created_at)
            """
        )


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def save_speedtest_result(result: SpeedtestResult) -> SpeedtestRecord:
    created_at = utc_now_iso()
    server = result.server

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO speedtest_results (
                created_at,
                download_bandwidth_bytes_per_second,
                download_bits_per_second,
                download_mbps,
                upload_bandwidth_bytes_per_second,
                upload_bits_per_second,
                upload_mbps,
                ping_latency_ms,
                ping_jitter_ms,
                server_id,
                server_name,
                server_location,
                server_country,
                server_host,
                isp,
                result_url
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                created_at,
                result.download.bandwidth_bytes_per_second,
                result.download.bits_per_second,
                result.download.mbps,
                result.upload.bandwidth_bytes_per_second,
                result.upload.bits_per_second,
                result.upload.mbps,
                result.ping.latency_ms,
                result.ping.jitter_ms,
                server.id if server else None,
                server.name if server else None,
                server.location if server else None,
                server.country if server else None,
                server.host if server else None,
                result.isp,
                result.result_url,
            ),
        )
        record_id = int(cursor.lastrowid)

    return SpeedtestRecord(id=record_id, created_at=created_at, **result.model_dump())


def list_speedtest_points(limit: int) -> list[SpeedtestTimeSeriesPoint]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM (
                SELECT
                    id,
                    created_at,
                    download_mbps,
                    upload_mbps,
                    ping_latency_ms,
                    ping_jitter_ms,
                    isp,
                    server_name,
                    server_location,
                    server_country
                FROM speedtest_results
                ORDER BY created_at DESC, id DESC
                LIMIT ?
            )
            ORDER BY created_at ASC, id ASC
            """,
            (limit,),
        ).fetchall()

    return [_row_to_time_series_point(row) for row in rows]


def _row_to_time_series_point(row: sqlite3.Row) -> SpeedtestTimeSeriesPoint:
    payload: dict[str, Any] = dict(row)
    return SpeedtestTimeSeriesPoint(**payload)
