"""Unit and integration tests for the /healthz endpoint."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_healthz_endpoint(client: AsyncClient) -> None:
    """Assert /healthz returns 200 OK and reports valid system status."""
    response = await client.get("/healthz")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "timestamp" in data
    assert data["database_connected"] is True


@pytest.mark.asyncio
async def test_api_v1_healthz_endpoint(client: AsyncClient) -> None:
    """Assert /api/v1/healthz prefix also returns 200 OK."""
    response = await client.get("/api/v1/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient) -> None:
    """Assert root endpoint / returns 200 OK with operational metadata."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "ASTRA-GUARD"
    assert data["status"] == "operational"
    assert data["health"] == "/healthz"
