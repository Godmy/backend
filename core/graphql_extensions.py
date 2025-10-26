"""
Strawberry GraphQL extensions для управления жизненным циклом ресурсов
"""

from typing import Any, Callable, Union

from strawberry.extensions import SchemaExtension
from strawberry.types import ExecutionContext

from core.database import SessionLocal
from core.structured_logging import get_logger

logger = get_logger(__name__)


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

        # Log GraphQL operation details
        operation_name = getattr(execution_context, 'operation_name', None)
        logger.debug(
            "GraphQL operation started",
            extra={
                "operation": operation_name,
                "event": "graphql_operation_start"
            }
        )

    def on_executing_end(self) -> None:
        """Вызывается в конце выполнения GraphQL операции"""
        # Получаем сессию из контекста
        execution_context: ExecutionContext = self.execution_context
        db = execution_context.context.get("db")
        operation_name = getattr(execution_context, 'operation_name', None)

        if db:
            try:
                # Закрываем сессию
                db.close()
                logger.debug(
                    "GraphQL operation completed",
                    extra={
                        "operation": operation_name,
                        "event": "graphql_operation_end"
                    }
                )
            except Exception as e:
                logger.error(
                    "Error closing DB session after GraphQL operation",
                    extra={
                        "operation": operation_name,
                        "error": str(e),
                        "event": "graphql_session_close_error"
                    },
                    exc_info=True
                )
