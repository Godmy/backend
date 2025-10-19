"""
Integration tests для GraphQL API поиска
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app import app
from languages.models.concept import ConceptModel
from languages.models.dictionary import DictionaryModel
from languages.models.language import LanguageModel


@pytest.fixture
def setup_test_data(db_session: Session):
    """Создать тестовые данные для GraphQL тестов"""
    # Создаем языки
    ru = LanguageModel(code="ru", name="Русский")
    en = LanguageModel(code="en", name="English")
    db_session.add_all([ru, en])
    db_session.flush()

    # Создаем концепции
    colors = ConceptModel(path="colors", depth=0, parent_id=None)
    db_session.add(colors)
    db_session.flush()

    red = ConceptModel(path="colors.red", depth=1, parent_id=colors.id)
    blue = ConceptModel(path="colors.blue", depth=1, parent_id=colors.id)
    db_session.add_all([red, blue])
    db_session.flush()

    # Создаем переводы
    dictionaries = [
        DictionaryModel(
            concept_id=colors.id, language_id=ru.id, name="Цвета", description="Категория цветов"
        ),
        DictionaryModel(
            concept_id=colors.id, language_id=en.id, name="Colors", description="Color category"
        ),
        DictionaryModel(
            concept_id=red.id, language_id=ru.id, name="Красный", description="Цвет огня"
        ),
        DictionaryModel(
            concept_id=red.id, language_id=en.id, name="Red", description="Color of fire"
        ),
        DictionaryModel(
            concept_id=blue.id, language_id=ru.id, name="Синий", description="Цвет неба"
        ),
        DictionaryModel(
            concept_id=blue.id, language_id=en.id, name="Blue", description="Color of sky"
        ),
    ]
    db_session.add_all(dictionaries)
    db_session.commit()

    return {
        "languages": {"ru": ru, "en": en},
        "concepts": {"colors": colors, "red": red, "blue": blue},
    }


@pytest.mark.asyncio
async def test_search_concepts_query_exists():
    """Тест что searchConcepts query существует"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        query = """
        {
            __type(name: "Query") {
                fields {
                    name
                }
            }
        }
        """
        response = await client.post("/graphql", json={"query": query})
        assert response.status_code == 200
        data = response.json()
        field_names = [field["name"] for field in data["data"]["__type"]["fields"]]
        assert "searchConcepts" in field_names


@pytest.mark.asyncio
async def test_search_without_filters(setup_test_data):
    """Тест поиска без фильтров"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        query = """
        query {
            searchConcepts(filters: {}) {
                total
                hasMore
                results {
                    concept {
                        id
                        path
                    }
                    dictionaries {
                        name
                        languageId
                    }
                }
            }
        }
        """
        response = await client.post("/graphql", json={"query": query})
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        search_result = data["data"]["searchConcepts"]
        assert search_result["total"] >= 3
        assert len(search_result["results"]) >= 3


@pytest.mark.asyncio
async def test_search_by_query_text(setup_test_data):
    """Тест поиска по тексту"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        query = """
        query {
            searchConcepts(filters: { query: "fire" }) {
                total
                results {
                    concept {
                        path
                    }
                    dictionaries {
                        name
                        description
                    }
                }
            }
        }
        """
        response = await client.post("/graphql", json={"query": query})
        assert response.status_code == 200
        data = response.json()
        search_result = data["data"]["searchConcepts"]
        assert search_result["total"] >= 1
        # Проверяем что нашли red (fire in description)
        paths = [r["concept"]["path"] for r in search_result["results"]]
        assert "colors.red" in paths


@pytest.mark.asyncio
async def test_search_with_language_filter(setup_test_data):
    """Тест поиска с фильтром по языку"""
    ru_id = setup_test_data["languages"]["ru"].id

    async with AsyncClient(app=app, base_url="http://test") as client:
        query = f"""
        query {{
            searchConcepts(filters: {{ languageIds: [{ru_id}] }}) {{
                total
                results {{
                    concept {{
                        path
                    }}
                    dictionaries {{
                        name
                        languageId
                    }}
                }}
            }}
        }}
        """
        response = await client.post("/graphql", json={"query": query})
        assert response.status_code == 200
        data = response.json()
        search_result = data["data"]["searchConcepts"]
        # Все словари должны быть на русском
        for result in search_result["results"]:
            for dictionary in result["dictionaries"]:
                assert dictionary["languageId"] == ru_id


@pytest.mark.asyncio
async def test_search_with_category_filter(setup_test_data):
    """Тест поиска с фильтром по категории"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        query = """
        query {
            searchConcepts(filters: { categoryPath: "colors" }) {
                total
                results {
                    concept {
                        path
                    }
                }
            }
        }
        """
        response = await client.post("/graphql", json={"query": query})
        assert response.status_code == 200
        data = response.json()
        search_result = data["data"]["searchConcepts"]
        assert search_result["total"] == 3  # colors, colors.red, colors.blue
        paths = [r["concept"]["path"] for r in search_result["results"]]
        assert all("colors" in p for p in paths)


@pytest.mark.asyncio
async def test_search_with_pagination(setup_test_data):
    """Тест пагинации"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Первая страница
        query1 = """
        query {
            searchConcepts(filters: { limit: 2, offset: 0 }) {
                total
                hasMore
                limit
                offset
                results {
                    concept {
                        id
                    }
                }
            }
        }
        """
        response1 = await client.post("/graphql", json={"query": query1})
        data1 = response1.json()
        result1 = data1["data"]["searchConcepts"]

        assert result1["limit"] == 2
        assert result1["offset"] == 0
        assert len(result1["results"]) <= 2
        assert result1["hasMore"] == ((0 + 2) < result1["total"])

        # Вторая страница
        query2 = """
        query {
            searchConcepts(filters: { limit: 2, offset: 2 }) {
                results {
                    concept {
                        id
                    }
                }
            }
        }
        """
        response2 = await client.post("/graphql", json={"query": query2})
        data2 = response2.json()
        result2 = data2["data"]["searchConcepts"]

        # ID должны быть разными
        ids1 = [r["concept"]["id"] for r in result1["results"]]
        ids2 = [r["concept"]["id"] for r in result2["results"]]
        assert len(set(ids1) & set(ids2)) == 0


@pytest.mark.asyncio
async def test_search_with_sorting(setup_test_data):
    """Тест различных вариантов сортировки"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Сортировка по алфавиту
        query_alphabet = """
        query {
            searchConcepts(filters: { sortBy: ALPHABET }) {
                results {
                    concept {
                        path
                    }
                }
            }
        }
        """
        response = await client.post("/graphql", json={"query": query_alphabet})
        data = response.json()
        paths = [r["concept"]["path"] for r in data["data"]["searchConcepts"]["results"]]
        assert paths == sorted(paths)

        # Сортировка по дате
        query_date = """
        query {
            searchConcepts(filters: { sortBy: DATE }) {
                results {
                    concept {
                        id
                    }
                }
            }
        }
        """
        response = await client.post("/graphql", json={"query": query_date})
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_search_combined_filters(setup_test_data):
    """Тест комбинации фильтров"""
    en_id = setup_test_data["languages"]["en"].id

    async with AsyncClient(app=app, base_url="http://test") as client:
        query = f"""
        query {{
            searchConcepts(filters: {{
                query: "color"
                languageIds: [{en_id}]
                categoryPath: "colors"
                sortBy: ALPHABET
                limit: 10
            }}) {{
                total
                results {{
                    concept {{
                        path
                    }}
                    dictionaries {{
                        name
                        languageId
                    }}
                }}
            }}
        }}
        """
        response = await client.post("/graphql", json={"query": query})
        assert response.status_code == 200
        data = response.json()
        search_result = data["data"]["searchConcepts"]

        # Проверяем фильтры
        for result in search_result["results"]:
            # Все из категории colors
            assert "colors" in result["concept"]["path"]
            # Все словари на английском
            for dictionary in result["dictionaries"]:
                assert dictionary["languageId"] == en_id
