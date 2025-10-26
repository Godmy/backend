"""
Strawberry GraphQL extensions для управления жизненным циклом ресурсов
"""

import logging
from typing import Any, Callable, Union

from strawberry.extensions import SchemaExtension
from strawberry.types import ExecutionContext

from core.database import SessionLocal

logger = logging.getLogger(__name__)


class DatabaseSessionExtension(SchemaExtension):
    """
    Extension для автоматического управления DB сессиями в GraphQL запросах.

    Создает DB сессию в начале каждого запроса и гарантированно закрывает её
    в конце, даже если произошла ошибка.
    """

    def on_executing_start(self) -> None:
        """Вызывается в начале выполнения GraphQL операции"""
        # Создаем новую DB сессию
        db = SessionLocal()

        # Сохраняем сессию в контексте выполнения
        execution_context: ExecutionContext = self.execution_context
        execution_context.context["db"] = db

        logger.debug(f"DB session created for GraphQL request")

    def on_executing_end(self) -> None:
        """Вызывается в конце выполнения GraphQL операции"""
        # Получаем сессию из контекста
        execution_context: ExecutionContext = self.execution_context
        db = execution_context.context.get("db")

        if db:
            try:
                # Закрываем сессию
                db.close()
                logger.debug("DB session closed after GraphQL request")
            except Exception as e:
                logger.error(f"Error closing DB session: {e}")
