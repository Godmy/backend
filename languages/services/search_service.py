"""
Сервис для поиска концепций и переводов
Implements full-text search with filters, sorting, and pagination
"""

from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import and_, asc, desc, func, or_
from sqlalchemy.orm import Session, joinedload

from languages.models.concept import ConceptModel
from languages.models.dictionary import DictionaryModel


class SearchService:
    """Сервис для поиска концепций с фильтрацией и сортировкой"""

    def __init__(self, db: Session):
        self.db = db

    def search_concepts(
        self,
        query: Optional[str] = None,
        language_ids: Optional[List[int]] = None,
        category_path: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        sort_by: str = "relevance",
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[ConceptModel], int]:
        """
        Поиск концепций с фильтрацией и пагинацией

        Args:
            query: Поисковый запрос (ищет в name и description словарей)
            language_ids: Фильтр по языкам
            category_path: Фильтр по пути концепции (префикс)
            from_date: Фильтр по дате создания (от)
            to_date: Фильтр по дате создания (до)
            sort_by: Сортировка (relevance, alphabet, date)
            limit: Количество результатов на странице
            offset: Смещение для пагинации

        Returns:
            Tuple[List[ConceptModel], int]: (список концепций, общее количество)
        """
        # Базовый запрос с загрузкой связанных словарей
        base_query = self.db.query(ConceptModel).distinct()

        # Подзапрос для поиска в словарях
        subquery_filters = []

        # Full-text search в словарях
        if query:
            search_term = f"%{query.lower()}%"
            subquery_filters.append(
                or_(
                    func.lower(DictionaryModel.name).like(search_term),
                    func.lower(DictionaryModel.description).like(search_term),
                )
            )

        # Фильтр по языкам
        if language_ids:
            subquery_filters.append(DictionaryModel.language_id.in_(language_ids))

        # Если есть фильтры по словарям, делаем join
        if subquery_filters:
            base_query = base_query.join(
                DictionaryModel, ConceptModel.id == DictionaryModel.concept_id
            ).filter(and_(*subquery_filters))

        # Фильтр по категории (path prefix)
        if category_path:
            base_query = base_query.filter(ConceptModel.path.like(f"{category_path}%"))

        # Фильтр по дате создания
        if from_date:
            base_query = base_query.filter(ConceptModel.created_at >= from_date)
        if to_date:
            base_query = base_query.filter(ConceptModel.created_at <= to_date)

        # Подсчет общего количества
        total = base_query.count()

        # Сортировка
        if sort_by == "alphabet":
            # Сортировка по пути (алфавитная)
            base_query = base_query.order_by(asc(ConceptModel.path))
        elif sort_by == "date":
            # Сортировка по дате создания (новые первые)
            base_query = base_query.order_by(desc(ConceptModel.created_at))
        else:  # relevance
            # Для релевантности используем порядок по глубине и пути
            # Более специфичные концепции (большая глубина) выше
            if query:
                base_query = base_query.order_by(desc(ConceptModel.depth), asc(ConceptModel.path))
            else:
                # Без запроса просто сортируем по пути
                base_query = base_query.order_by(asc(ConceptModel.path))

        # Пагинация
        concepts = (
            base_query.options(joinedload(ConceptModel.dictionaries))
            .limit(limit)
            .offset(offset)
            .all()
        )

        return concepts, total

    def get_concept_with_dictionaries(self, concept_id: int) -> Optional[ConceptModel]:
        """
        Получить концепцию с загруженными словарями

        Args:
            concept_id: ID концепции

        Returns:
            ConceptModel с загруженными dictionaries или None
        """
        return (
            self.db.query(ConceptModel)
            .options(joinedload(ConceptModel.dictionaries))
            .filter(ConceptModel.id == concept_id)
            .first()
        )

    def get_matching_dictionaries(
        self, concept_id: int, language_ids: Optional[List[int]] = None
    ) -> List[DictionaryModel]:
        """
        Получить словари для концепции с фильтрацией по языкам

        Args:
            concept_id: ID концепции
            language_ids: Фильтр по языкам (опционально)

        Returns:
            Список словарей
        """
        query = self.db.query(DictionaryModel).filter(DictionaryModel.concept_id == concept_id)

        if language_ids:
            query = query.filter(DictionaryModel.language_id.in_(language_ids))

        return query.all()
