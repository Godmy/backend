"""
Тесты для проверки функциональности GraphQL Playground
"""
import pytest
import os
from starlette.testclient import TestClient
from unittest.mock import patch, MagicMock

# Импортируем компоненты приложения
from core.database import engine
from core.init_db import init_database
from auth.utils.jwt_handler import jwt_handler
import app as app_module


@pytest.fixture
def client():
    """Тестовый клиент для приложения"""
    return TestClient(app)


@pytest.mark.asyncio
async def test_graphql_playground_enabled():
    """Тестирование доступности GraphQL Playground"""
    # Установим переменную окружения для включения Playground
    os.environ["GRAPHQL_PLAYGROUND_ENABLED"] = "true"
    
    with TestClient(app) as client:
        response = client.get("/graphql")
        assert response.status_code == 200
        assert "GraphiQL" in response.text or "GraphQL" in response.text
        

def test_graphql_playground_examples():
    """Тестирование эндпоинта с примерами запросов"""
    with TestClient(app) as client:
        response = client.get("/graphql/examples")
        assert response.status_code == 200
        
        data = response.json()
        assert "queries" in data
        assert "mutations" in data
        assert isinstance(data["queries"], dict)
        assert isinstance(data["mutations"], dict)


def test_graphql_playground_test_user_login_dev_mode():
    """Тестирование эндпоинта получения тестового токена в dev режиме"""
    # Установим режим разработки
    original_env = os.environ.get("ENVIRONMENT")
    os.environ["ENVIRONMENT"] = "development"
    
    try:
        with TestClient(app) as client:
            response = client.get("/graphql/test-user-login")
            assert response.status_code == 200
            
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data
            assert "user" in data
            assert data["user"]["username"] == "test_user"
    finally:
        # Восстановим оригинальное значение
        if original_env is not None:
            os.environ["ENVIRONMENT"] = original_env
        else:
            del os.environ["ENVIRONMENT"]


def test_graphql_playground_test_user_login_prod_mode():
    """Тестирование что эндпоинт тестового пользователя недоступен в prod режиме"""
    # Установим режим продакшн
    original_env = os.environ.get("ENVIRONMENT")
    os.environ["ENVIRONMENT"] = "production"
    
    try:
        with TestClient(app) as client:
            response = client.get("/graphql/test-user-login")
            assert response.status_code == 403
            
            data = response.json()
            assert "error" in data
            assert "development" in data["error"]
    finally:
        # Восстановим оригинальное значение
        if original_env is not None:
            os.environ["ENVIRONMENT"] = original_env
        else:
            del os.environ["ENVIRONMENT"]


def test_graphql_query_with_custom_headers():
    """Тестирование GraphQL запроса с кастомными заголовками"""
    with TestClient(app) as client:
        # Простой запрос для проверки работоспособности GraphQL
        query = """
        query {
            __schema {
                queryType { name }
            }
        }
        """
        
        response = client.post(
            "/graphql",
            json={"query": query},
            headers={"X-GraphQL-Client": "Playground"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert data["data"]["__schema"]["queryType"]["name"] is not None