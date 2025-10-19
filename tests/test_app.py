import pytest
from httpx import AsyncClient

from app import app


@pytest.mark.asyncio
async def test_health_check():
    """Test the health check endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_graphql_endpoint_exists():
    """Test that GraphQL endpoint is accessible"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Simple introspection query
        query = """
        {
            __schema {
                queryType {
                    name
                }
            }
        }
        """
        response = await client.post("/graphql", json={"query": query})
        assert response.status_code == 200
        data = response.json()
        assert "data" in data


@pytest.mark.asyncio
async def test_root_redirects_to_graphql():
    """Test that root path redirects to GraphQL"""
    async with AsyncClient(app=app, base_url="http://test", follow_redirects=False) as client:
        response = await client.get("/")
        assert response.status_code == 307  # Temporary redirect
        assert response.headers["location"] == "/graphql"
