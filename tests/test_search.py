"""
Тесты для функциональности поиска концепций
"""

from datetime import datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from languages.models.concept import ConceptModel
from languages.models.dictionary import DictionaryModel
from languages.models.language import LanguageModel
from languages.services.search_service import SearchService


@pytest.fixture
def search_service(db_session: Session):
    """Фикстура для SearchService"""
    return SearchService(db_session)


@pytest.fixture
def test_data(db_session: Session):
    """Создать тестовые данные для поиска"""
    # Создаем языки
    ru = LanguageModel(code="ru", name="Русский")
    en = LanguageModel(code="en", name="English")
    es = LanguageModel(code="es", name="Español")
    db_session.add_all([ru, en, es])
    db_session.flush()

    # Создаем концепции
    colors = ConceptModel(path="colors", depth=0, parent_id=None)
    animals = ConceptModel(path="animals", depth=0, parent_id=None)
    db_session.add_all([colors, animals])
    db_session.flush()

    red = ConceptModel(path="colors.red", depth=1, parent_id=colors.id)
    blue = ConceptModel(path="colors.blue", depth=1, parent_id=colors.id)
    cat = ConceptModel(path="animals.cat", depth=1, parent_id=animals.id)
    dog = ConceptModel(path="animals.dog", depth=1, parent_id=animals.id)
    db_session.add_all([red, blue, cat, dog])
    db_session.flush()

    # Создаем переводы
    dictionaries = [
        # Colors
        DictionaryModel(
            concept_id=colors.id,
            language_id=ru.id,
            name="Цвета",
            description="Категория цветов",
        ),
        DictionaryModel(
            concept_id=colors.id, language_id=en.id, name="Colors", description="Color category"
        ),
        # Red
        DictionaryModel(
            concept_id=red.id,
            language_id=ru.id,
            name="Красный",
            description="Цвет крови и огня",
        ),
        DictionaryModel(
            concept_id=red.id,
            language_id=en.id,
            name="Red",
            description="Color of blood and fire",
        ),
        DictionaryModel(
            concept_id=red.id, language_id=es.id, name="Rojo", description="Color de sangre"
        ),
        # Blue
        DictionaryModel(
            concept_id=blue.id, language_id=ru.id, name="Синий", description="Цвет неба и моря"
        ),
        DictionaryModel(
            concept_id=blue.id,
            language_id=en.id,
            name="Blue",
            description="Color of sky and ocean",
        ),
        # Animals
        DictionaryModel(
            concept_id=animals.id,
            language_id=ru.id,
            name="Животные",
            description="Категория животных",
        ),
        DictionaryModel(
            concept_id=animals.id,
            language_id=en.id,
            name="Animals",
            description="Animal category",
        ),
        # Cat
        DictionaryModel(
            concept_id=cat.id,
            language_id=ru.id,
            name="Кошка",
            description="Домашнее животное семейства кошачьих",
        ),
        DictionaryModel(
            concept_id=cat.id,
            language_id=en.id,
            name="Cat",
            description="Domestic feline animal",
        ),
        # Dog
        DictionaryModel(
            concept_id=dog.id,
            language_id=ru.id,
            name="Собака",
            description="Домашнее животное, друг человека",
        ),
        DictionaryModel(
            concept_id=dog.id, language_id=en.id, name="Dog", description="Man's best friend"
        ),
    ]

    db_session.add_all(dictionaries)
    db_session.commit()

    return {
        "languages": {"ru": ru, "en": en, "es": es},
        "concepts": {
            "colors": colors,
            "animals": animals,
            "red": red,
            "blue": blue,
            "cat": cat,
            "dog": dog,
        },
    }


class TestSearchService:
    """Тесты для SearchService"""

    def test_search_without_query(self, search_service, test_data):
        """Тест поиска без поискового запроса (вернуть все)"""
        concepts, total = search_service.search_concepts()
        assert total == 6  # All concepts
        assert len(concepts) == 6

    def test_search_by_name(self, search_service, test_data):
        """Тест поиска по имени"""
        concepts, total = search_service.search_concepts(query="cat")
        assert total >= 1
        # Проверяем что нашли концепцию кошки
        paths = [c.path for c in concepts]
        assert "animals.cat" in paths

    def test_search_by_description(self, search_service, test_data):
        """Тест поиска по описанию"""
        concepts, total = search_service.search_concepts(query="blood")
        assert total >= 1
        paths = [c.path for c in concepts]
        assert "colors.red" in paths

    def test_search_case_insensitive(self, search_service, test_data):
        """Тест поиска без учета регистра"""
        concepts1, total1 = search_service.search_concepts(query="RED")
        concepts2, total2 = search_service.search_concepts(query="red")
        assert total1 == total2
        assert len(concepts1) == len(concepts2)

    def test_filter_by_language(self, search_service, test_data):
        """Тест фильтрации по языку"""
        ru_id = test_data["languages"]["ru"].id
        es_id = test_data["languages"]["es"].id

        # Поиск только в русском
        concepts, total = search_service.search_concepts(query="красный", language_ids=[ru_id])
        assert total >= 1

        # Поиск только в испанском (есть только для red)
        concepts, total = search_service.search_concepts(language_ids=[es_id])
        assert total == 1
        assert concepts[0].path == "colors.red"

    def test_filter_by_category_path(self, search_service, test_data):
        """Тест фильтрации по пути категории"""
        # Только цвета
        concepts, total = search_service.search_concepts(category_path="colors")
        assert total == 3  # colors, colors.red, colors.blue
        paths = [c.path for c in concepts]
        assert all("colors" in p for p in paths)

        # Только животные
        concepts, total = search_service.search_concepts(category_path="animals")
        assert total == 3  # animals, animals.cat, animals.dog
        paths = [c.path for c in concepts]
        assert all("animals" in p for p in paths)

    def test_filter_by_date(self, search_service, test_data):
        """Тест фильтрации по дате создания"""
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        tomorrow = now + timedelta(days=1)

        # Все созданы сегодня
        concepts, total = search_service.search_concepts(from_date=yesterday, to_date=tomorrow)
        assert total == 6

        # Ничего не создано завтра
        concepts, total = search_service.search_concepts(from_date=tomorrow)
        assert total == 0

    def test_sort_by_alphabet(self, search_service, test_data):
        """Тест сортировки по алфавиту"""
        concepts, _ = search_service.search_concepts(sort_by="alphabet")
        paths = [c.path for c in concepts]
        # Проверяем что paths отсортированы
        assert paths == sorted(paths)

    def test_sort_by_date(self, search_service, test_data):
        """Тест сортировки по дате (новые первые)"""
        concepts, _ = search_service.search_concepts(sort_by="date")
        dates = [c.created_at for c in concepts]
        # Проверяем что даты в убывающем порядке
        assert dates == sorted(dates, reverse=True)

    def test_sort_by_relevance(self, search_service, test_data):
        """Тест сортировки по релевантности"""
        concepts, _ = search_service.search_concepts(query="color", sort_by="relevance")
        # Более специфичные концепции (большая глубина) должны быть выше
        assert len(concepts) > 0
        # Первые результаты должны иметь большую глубину
        depths = [c.depth for c in concepts[:3]]
        assert any(d > 0 for d in depths)

    def test_pagination(self, search_service, test_data):
        """Тест пагинации"""
        # Первая страница (2 элемента)
        concepts1, total = search_service.search_concepts(limit=2, offset=0, sort_by="alphabet")
        assert len(concepts1) == 2
        assert total == 6

        # Вторая страница
        concepts2, _ = search_service.search_concepts(limit=2, offset=2, sort_by="alphabet")
        assert len(concepts2) == 2

        # Проверяем что разные
        ids1 = [c.id for c in concepts1]
        ids2 = [c.id for c in concepts2]
        assert len(set(ids1) & set(ids2)) == 0

    def test_combined_filters(self, search_service, test_data):
        """Тест комбинации фильтров"""
        en_id = test_data["languages"]["en"].id

        # Поиск "color" только в английском языке в категории colors
        concepts, total = search_service.search_concepts(
            query="color", language_ids=[en_id], category_path="colors", limit=10
        )

        assert total >= 1
        # Проверяем что все результаты из категории colors
        paths = [c.path for c in concepts]
        assert all("colors" in p for p in paths)

    def test_get_concept_with_dictionaries(self, search_service, test_data):
        """Тест получения концепции с загруженными словарями"""
        cat_id = test_data["concepts"]["cat"].id
        concept = search_service.get_concept_with_dictionaries(cat_id)

        assert concept is not None
        assert concept.id == cat_id
        assert len(concept.dictionaries) >= 2  # ru и en

    def test_get_matching_dictionaries(self, search_service, test_data):
        """Тест получения словарей с фильтрацией"""
        red_id = test_data["concepts"]["red"].id
        ru_id = test_data["languages"]["ru"].id
        en_id = test_data["languages"]["en"].id

        # Все словари для red
        all_dicts = search_service.get_matching_dictionaries(red_id)
        assert len(all_dicts) == 3  # ru, en, es

        # Только русский и английский
        filtered_dicts = search_service.get_matching_dictionaries(
            red_id, language_ids=[ru_id, en_id]
        )
        assert len(filtered_dicts) == 2
        lang_ids = [d.language_id for d in filtered_dicts]
        assert ru_id in lang_ids
        assert en_id in lang_ids
