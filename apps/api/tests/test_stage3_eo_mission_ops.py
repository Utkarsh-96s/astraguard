"""Unit and integration tests for Stage 3 - Earth Observation & Mission Ops.

Tests F7 (Disaster Intelligence Deck & Multi-Hazard scenarios),
F8 & F11 (Constellation Mode & Multi-Asset Conjunction Matrix),
and F9 (Live Telemetry Streamer).
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_disaster_deck_catalog(client: AsyncClient) -> None:
    """Test GET /api/v1/events/disaster-deck returns multi-hazard EO scenarios."""
    res = await client.get("/api/v1/events/disaster-deck")
    assert res.status_code == 200
    data = res.json()

    assert data["count"] >= 4
    scenarios = data["scenarios"]
    scenario_ids = [s["id"] for s in scenarios]

    assert "DIS-EMILIA-FLOOD-2023" in scenario_ids
    assert "DIS-BRAHMAPUTRA-01" in scenario_ids
    assert "DIS-GREECE-EVROS-2023" in scenario_ids
    assert "DIS-VALENCIA-FLASH-2024" in scenario_ids

    # Verify sensor diversity (SAR and Optical)
    modalities = {s["sensor_type"] for s in scenarios}
    assert "radar" in modalities
    assert "optical" in modalities

    # Verify GeoJSON polygon format
    emilia = next(s for s in scenarios if s["id"] == "DIS-EMILIA-FLOOD-2023")
    assert emilia["geojson_footprint"]["type"] == "Feature"
    assert emilia["geojson_footprint"]["geometry"]["type"] == "Polygon"
    assert len(emilia["geojson_footprint"]["geometry"]["coordinates"][0]) == 5

    # Verify segmentation metrics and damage impact
    assert emilia["mean_iou"] > 0.90
    assert emilia["mean_dice"] > 0.95
    assert emilia["infrastructure_impact"]["bridges_critical"] > 0
    assert emilia["infrastructure_impact"]["substations_affected"] > 0


@pytest.mark.asyncio
async def test_disaster_scenario_detail(client: AsyncClient) -> None:
    """Test GET /api/v1/events/disaster-deck/{event_id} with valid and invalid IDs."""
    res = await client.get("/api/v1/events/disaster-deck/DIS-GREECE-EVROS-2023")
    assert res.status_code == 200
    evros = res.json()

    assert evros["id"] == "DIS-GREECE-EVROS-2023"
    assert evros["disaster_type"] == "wildfire"
    assert evros["area_km2"] == 935.0
    assert evros["priority"] >= 0.90
    assert "SWIR" in evros["polarization"]

    # 404 test for non-existent scenario
    res_404 = await client.get("/api/v1/events/disaster-deck/DIS-NONEXISTENT-999")
    assert res_404.status_code == 404


@pytest.mark.asyncio
async def test_constellation_matrix(client: AsyncClient) -> None:
    """Test GET /api/v1/assets/constellation-matrix returns fleet overview and conjunction threats."""
    res = await client.get("/api/v1/assets/constellation-matrix")
    assert res.status_code == 200
    data = res.json()

    assert data["fleet_size"] == 3
    assert data["aggregate_health_score"] >= 9.0
    assert data["fleet_risk_level"] == "NOMINAL"

    asset_ids = [a["id"] for a in data["assets"]]
    assert "SENTINEL-2A" in asset_ids
    assert "SENTINEL-1A" in asset_ids
    assert "SENTINEL-3A" in asset_ids

    # Cross-conjunctions list
    conj = data["cross_conjunctions"]
    assert len(conj) >= 3
    first_conj = conj[0]
    assert "primary_asset_id" in first_conj
    assert "secondary_name" in first_conj
    assert "miss_distance_m" in first_conj
    assert "pc" in first_conj
    assert "risk_class" in first_conj


@pytest.mark.asyncio
async def test_live_telemetry_stream(client: AsyncClient) -> None:
    """Test GET /api/v1/assets/{asset_id}/telemetry/live-stream returns streaming telemetry packet."""
    res = await client.get("/api/v1/assets/SENTINEL-2A/telemetry/live-stream?step=12")
    assert res.status_code == 200
    pkt = res.json()

    assert pkt["asset_id"] == "SENTINEL-2A"
    assert pkt["sequence_number"] == 12
    assert "channels" in pkt

    ch = pkt["channels"]
    assert "eps_battery_temp_c" in ch
    assert "eps_bus_voltage_v" in ch
    assert "eps_solar_array_current_a" in ch
    assert "adcs_reaction_wheel_rpm" in ch
    assert "obc_cpu_load_pct" in ch

    # Sensible spacecraft engineering ranges
    assert 15.0 <= ch["eps_battery_temp_c"] <= 35.0
    assert 25.0 <= ch["eps_bus_voltage_v"] <= 32.0
    assert 1000 <= ch["adcs_reaction_wheel_rpm"] <= 5000
    assert 10 <= ch["obc_cpu_load_pct"] <= 95


@pytest.mark.asyncio
async def test_constellation_fleet_subsystems(client: AsyncClient) -> None:
    """Test that all constellation assets report complete subsystem health."""
    res = await client.get("/api/v1/assets/constellation-matrix")
    assert res.status_code == 200
    assets = res.json()["assets"]

    for a in assets:
        assert a["health_score"] >= 9.0
        sub = a["subsystems"]
        assert "eps" in sub
        assert "thermal" in sub
        assert "adcs" in sub
        assert "obc" in sub
        assert "payload" in sub
        assert sub["eps"]["status"] == "NOMINAL"
        assert sub["payload"]["status"] == "ACTIVE"
