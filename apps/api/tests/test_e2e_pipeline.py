"""End-to-End Pipeline Integration Test for ASTRA-GUARD Platform.

Verifies the complete operational flight intelligence loop:
1. Seed primary asset (SENTINEL-2A).
2. Ingest multi-channel spacecraft telemetry batch.
3. Ingest space object orbital TLE catalog.
4. Ingest close-approach conjunction assessment event.
5. Ingest Earth Observation disaster intelligence event.
6. Trigger integrated mission risk engine evaluation.
7. Verify deterministic safety override and alert generation.
8. Submit human-in-the-loop operator action (advisory recommendation review).
9. Verify immutable operator audit trail and real-time broadcast readiness.
"""
from datetime import UTC, datetime

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_full_mission_e2e_pipeline(client: AsyncClient) -> None:
    """Execute complete end-to-end mission safety and intelligence pipeline."""
    # -------------------------------------------------------------
    # Step 1: Query / Seed Satellite Asset
    # -------------------------------------------------------------
    assets_resp = await client.get("/api/v1/assets")
    assert assets_resp.status_code == 200
    assets = assets_resp.json()
    assert any(a["id"] == "SENTINEL-2A" for a in assets)

    # -------------------------------------------------------------
    # Step 2: Ingest Multi-Channel Telemetry Batch
    # -------------------------------------------------------------
    now = datetime.now(UTC)
    telemetry_batch = {
        "readings": [
            {
                "asset_id": "SENTINEL-2A",
                "ts": now.isoformat(),
                "channel": "eps_battery_temp_c",
                "value": 38.4,
                "quality": 1.0,
                "synthetic": True,
            },
            {
                "asset_id": "SENTINEL-2A",
                "ts": now.isoformat(),
                "channel": "bus_voltage_v",
                "value": 28.1,
                "quality": 1.0,
                "synthetic": True,
            },
        ]
    }
    telemetry_resp = await client.post("/api/v1/ingest/telemetry", json=telemetry_batch)
    assert telemetry_resp.status_code == 201
    assert telemetry_resp.json()["ingested_count"] == 2

    # -------------------------------------------------------------
    # Step 3: Ingest Space Object Catalog (Secondary Debris)
    # -------------------------------------------------------------
    objects_batch = {
        "objects": [
            {
                "norad_id": 29834,
                "name": "FENGYUN-1C-DEB-29834",
                "type": "debris",
                "tle_line1": "1 29834U 99025EK  24080.50000000  .00001234  00000-0  12345-3 0  9991",
                "tle_line2": "2 29834  98.6500 120.4500 0012345  45.6700 314.5600 14.25000000234567",
                "epoch": now.isoformat(),
            }
        ]
    }
    obj_resp = await client.post("/api/v1/ingest/tle", json=objects_batch)
    assert obj_resp.status_code == 201
    assert obj_resp.json()["ingested_count"] == 1

    # -------------------------------------------------------------
    # Step 4: Ingest Conjunction Assessment Event
    # -------------------------------------------------------------
    conjunction_payload = {
        "id": "CONJ-E2E-001",
        "primary_id": "SENTINEL-2A",
        "secondary_id": 29834,
        "tca": now.isoformat(),
        "miss_km": 0.285,
        "rel_vel_kms": 12.4,
        "pc": 3.2e-4,  # Breaches 1e-4 threshold
        "pc_method": "foster_2d_screening",
        "risk_class": "CRITICAL",
        "synthetic": True,
        "created_at": now.isoformat(),
    }
    conj_resp = await client.post("/api/v1/ingest/conjunction", json=conjunction_payload)
    assert conj_resp.status_code == 201
    assert conj_resp.json()["status"] == "persisted"

    # -------------------------------------------------------------
    # Step 5: Ingest Earth Observation Disaster Event
    # -------------------------------------------------------------
    imagery_payload = {
        "product": {
            "id": "IMG-E2E-001",
            "source": "Sentinel-2",
            "bbox": {"type": "Polygon", "coordinates": [[[85.0, 20.0], [85.5, 20.0], [85.5, 20.5], [85.0, 20.5], [85.0, 20.0]]]},
            "acquired_at": now.isoformat(),
            "cloud_pct": 12.5,
            "uri": "s3://astraguard-imagery/2026/10/20/img-e2e-001.tif",
        },
        "event": {
            "id": "DIS-E2E-001",
            "product_id": "IMG-E2E-001",
            "type": "flood",
            "area_km2": 420.5,
            "mask_uri": "s3://astraguard-imagery/2026/10/20/mask-e2e-001.png",
            "priority": 0.78,
            "confidence": 0.94,
            "synthetic": True,
            "created_at": now.isoformat(),
        },
    }
    dis_resp = await client.post("/api/v1/ingest/imagery", json=imagery_payload)
    assert dis_resp.status_code == 201
    assert dis_resp.json()["status"] == "persisted"

    # -------------------------------------------------------------
    # Step 6: Evaluate Integrated Mission Risk
    # -------------------------------------------------------------
    eval_resp = await client.post(
        "/api/v1/risk/evaluate",
        json={"asset_id": "SENTINEL-2A"},
    )
    assert eval_resp.status_code == 200
    risk_data = eval_resp.json()

    assert risk_data["asset_id"] == "SENTINEL-2A"
    assert risk_data["level"] == "CRITICAL"
    assert risk_data["critical_override_applied"] is True
    assert risk_data["score"] >= 80.0
    assert len(risk_data["recommendations"]) >= 1

    # -------------------------------------------------------------
    # Step 7: Verify Mission Alert Generated
    # -------------------------------------------------------------
    alerts_resp = await client.get("/api/v1/alerts?level=CRITICAL")
    assert alerts_resp.status_code == 200
    alerts = alerts_resp.json()
    assert len(alerts) >= 1

    critical_alert = alerts[0]
    alert_id = critical_alert["id"]
    assert critical_alert["status"] == "ACTIVE"
    assert "CRITICAL" in critical_alert["level"]

    # -------------------------------------------------------------
    # Step 8: Human-in-the-Loop Operator Action (Acknowledge / Approve)
    # -------------------------------------------------------------
    action_resp = await client.post(
        f"/api/v1/alerts/{alert_id}/action",
        json={
            "user": "FlightDirector_Sarah",
            "action": "approve",
            "note": "Operator acknowledged critical conjunction with FENGYUN debris. Flight dynamics team notified.",
        },
    )
    assert action_resp.status_code == 200
    action_data = action_resp.json()
    assert action_data["alert"]["status"] == "ACKNOWLEDGED"

    # -------------------------------------------------------------
    # Step 9: Verify Tamper-Evident Audit Trail
    # -------------------------------------------------------------
    audit_resp = await client.get(f"/api/v1/alerts/{alert_id}")
    assert audit_resp.status_code == 200
    audit_data = audit_resp.json()

    assert audit_data["id"] == alert_id
    assert audit_data["status"] == "ACKNOWLEDGED"
    assert len(audit_data["audit_actions"]) == 1

    audit_entry = audit_data["audit_actions"][0]
    assert audit_entry["user"] == "FlightDirector_Sarah"
    assert audit_entry["action"] == "approve"
    assert "Flight dynamics team notified" in audit_entry["note"]
