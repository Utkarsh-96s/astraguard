"""Tests for ingestion and data query endpoints."""
from datetime import UTC, datetime

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_telemetry_ingest_and_query(client: AsyncClient) -> None:
    """Test POST /api/v1/ingest/telemetry and GET /api/v1/assets/{id}/telemetry."""
    now = datetime.now(UTC)
    readings = [
        {
            "asset_id": "SAT-TEST-99",
            "ts": now.isoformat(),
            "channel": "wheel_temp",
            "value": 24.5,
            "quality": 1.0,
            "synthetic": True,
        },
        {
            "asset_id": "SAT-TEST-99",
            "ts": now.isoformat(),
            "channel": "bus_current",
            "value": 14.1,
            "quality": 1.0,
            "synthetic": True,
        },
    ]

    # Ingest
    res = await client.post("/api/v1/ingest/telemetry", json={"readings": readings})
    assert res.status_code == 201
    data = res.json()
    assert data["ingested_count"] == 2
    assert data["asset_id"] == "SAT-TEST-99"
    assert data["synthetic"] is True

    # Query
    q_res = await client.get("/api/v1/assets/SAT-TEST-99/telemetry?channel=wheel_temp")
    assert q_res.status_code == 200
    q_data = q_res.json()
    assert q_data["count"] == 1
    assert q_data["data"][0]["channel"] == "wheel_temp"
    assert q_data["data"][0]["value"] == 24.5
    assert q_data["data"][0]["synthetic"] is True


@pytest.mark.asyncio
async def test_space_objects_ingest_and_query(client: AsyncClient) -> None:
    """Test POST /api/v1/ingest/tle and GET /api/v1/objects."""
    now = datetime.now(UTC)
    objects = [
        {
            "norad_id": 99901,
            "name": "TEST-DEBRIS-01",
            "type": "debris",
            "tle_line1": "1 99901U 20001A   26292.00000000  .00001000  00000-0  10000-3 0  9991",
            "tle_line2": "2 99901  98.5000 120.0000 0010000  80.0000 280.0000 14.3000000000001",
            "epoch": now.isoformat(),
        }
    ]

    res = await client.post("/api/v1/ingest/tle", json={"objects": objects})
    assert res.status_code == 201
    assert res.json()["ingested_count"] == 1

    # Query
    q_res = await client.get("/api/v1/objects?type=debris")
    assert q_res.status_code == 200
    q_data = q_res.json()
    assert q_data["count"] >= 1
    assert any(obj["norad_id"] == 99901 for obj in q_data["data"])


@pytest.mark.asyncio
async def test_disaster_ingest_and_query(client: AsyncClient) -> None:
    """Test POST /api/v1/ingest/imagery and GET /api/v1/events/disasters."""
    now = datetime.now(UTC)
    payload = {
        "product": {
            "id": "IMG-TEST-001",
            "source": "Sentinel-1",
            "bbox": {"min_lon": 10.0, "min_lat": 20.0, "max_lon": 11.0, "max_lat": 21.0},
            "acquired_at": now.isoformat(),
            "cloud_pct": 5.0,
            "uri": "data/test.png",
        },
        "event": {
            "id": "DISASTER-TEST-001",
            "product_id": "IMG-TEST-001",
            "type": "flood",
            "area_km2": 85.4,
            "mask_uri": "data/test_mask.png",
            "priority": 0.88,
            "confidence": 0.95,
            "synthetic": True,
            "created_at": now.isoformat(),
        },
    }

    res = await client.post("/api/v1/ingest/imagery", json=payload)
    assert res.status_code == 201
    assert res.json()["status"] == "persisted"

    # Query
    q_res = await client.get("/api/v1/events/disasters?type=flood")
    assert q_res.status_code == 200
    q_data = q_res.json()
    assert q_data["count"] >= 1
    assert any(ev["id"] == "DISASTER-TEST-001" for ev in q_data["data"])


@pytest.mark.asyncio
async def test_conjunction_ingest_and_query(client: AsyncClient) -> None:
    """Test POST /api/v1/ingest/conjunction and GET /api/v1/assets/{id}/conjunctions."""
    now = datetime.now(UTC)
    payload = {
        "id": "CONJ-TEST-001",
        "primary_id": "SAT-TEST-99",
        "secondary_id": 99901,
        "tca": now.isoformat(),
        "miss_km": 0.35,
        "rel_vel_kms": 14.1,
        "pc": 1.5e-4,
        "pc_method": "foster_2d_screening",
        "risk_class": "CRITICAL",
        "synthetic": True,
        "created_at": now.isoformat(),
    }

    res = await client.post("/api/v1/ingest/conjunction", json=payload)
    assert res.status_code == 201

    # Query
    q_res = await client.get("/api/v1/assets/SAT-TEST-99/conjunctions")
    assert q_res.status_code == 200
    q_data = q_res.json()
    assert q_data["count"] >= 1
    assert q_data["data"][0]["risk_class"] == "CRITICAL"
    assert q_data["data"][0]["synthetic"] is True
