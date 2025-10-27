"""
Database Statistics Utilities
Утилиты для сбора статистики по таблицам базы данных
"""

import logging
from typing import Dict, List, Optional

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from core.database import Base, engine

logger = logging.getLogger(__name__)


def get_table_count(db: Session, table_name: str) -> int:
    """
    Получить количество записей в таблице

    Args:
        db: Database session
        table_name: Имя таблицы

    Returns:
        Количество записей
    """
    try:
        result = db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        count = result.scalar()
        return count if count is not None else 0
    except Exception as e:
        logger.warning(f"Failed to get count for table {table_name}: {e}")
        return 0


def get_all_table_counts(db: Session) -> Dict[str, int]:
    """
    Получить количество записей во всех таблицах

    Args:
        db: Database session

    Returns:
        Словарь {table_name: count}
    """
    inspector = inspect(engine)
    table_names = inspector.get_table_names()

    counts = {}
    for table_name in table_names:
        counts[table_name] = get_table_count(db, table_name)

    return counts


def log_table_statistics(
    db: Session,
    tables: Optional[List[str]] = None,
    title: str = "Database Statistics"
) -> Dict[str, int]:
    """
    Логировать статистику по таблицам

    Args:
        db: Database session
        tables: Список конкретных таблиц (если None - все таблицы)
        title: Заголовок для логов

    Returns:
        Словарь {table_name: count}
    """
    logger.info("=" * 70)
    logger.info(f"{title:^70}")
    logger.info("=" * 70)

    if tables:
        counts = {table: get_table_count(db, table) for table in tables}
    else:
        counts = get_all_table_counts(db)

    # Сортируем таблицы по имени
    sorted_tables = sorted(counts.items())

    # Определяем максимальную длину имени таблицы для выравнивания
    max_len = max(len(name) for name, _ in sorted_tables) if sorted_tables else 0

    total_records = 0
    for table_name, count in sorted_tables:
        logger.info(f"  {table_name:<{max_len}} : {count:>8,} records")
        total_records += count

    logger.info("-" * 70)
    logger.info(f"  {'TOTAL':<{max_len}} : {total_records:>8,} records")
    logger.info("=" * 70)

    return counts


def log_table_change(
    table_name: str,
    before_count: int,
    after_count: int,
    created: int = 0,
    updated: int = 0,
    skipped: int = 0
) -> None:
    """
    Логировать изменения в таблице

    Args:
        table_name: Имя таблицы
        before_count: Количество записей до операции
        after_count: Количество записей после операции
        created: Количество созданных записей
        updated: Количество обновленных записей
        skipped: Количество пропущенных записей
    """
    delta = after_count - before_count

    logger.info(f"  📊 Table: {table_name}")
    logger.info(f"     Before:  {before_count:>6,} records")
    logger.info(f"     After:   {after_count:>6,} records")

    if created > 0:
        logger.info(f"     ✅ Created: {created:>6,} records")
    if updated > 0:
        logger.info(f"     🔄 Updated: {updated:>6,} records")
    if skipped > 0:
        logger.info(f"     ⊘ Skipped: {skipped:>6,} records")

    if delta > 0:
        logger.info(f"     📈 Delta:   +{delta:>6,} records")
    elif delta < 0:
        logger.info(f"     📉 Delta:   {delta:>6,} records")
    else:
        logger.info(f"     ➡️  Delta:   {delta:>6,} records (no change)")


class TableStatsTracker:
    """
    Класс для отслеживания изменений в таблицах

    Usage:
        tracker = TableStatsTracker(db, ["users", "roles"])
        tracker.log_before("Starting user creation")

        # ... create users ...

        tracker.log_after("Users created", created=10, skipped=5)
    """

    def __init__(self, db: Session, tables: List[str]):
        """
        Инициализация трекера

        Args:
            db: Database session
            tables: Список таблиц для отслеживания
        """
        self.db = db
        self.tables = tables
        self.before_counts: Dict[str, int] = {}
        self.after_counts: Dict[str, int] = {}

    def log_before(self, title: str = "Before Operation") -> Dict[str, int]:
        """
        Логировать состояние таблиц до операции

        Args:
            title: Заголовок для логов

        Returns:
            Словарь {table_name: count}
        """
        self.before_counts = log_table_statistics(self.db, self.tables, title)
        return self.before_counts

    def log_after(
        self,
        title: str = "After Operation",
        created: int = 0,
        updated: int = 0,
        skipped: int = 0
    ) -> Dict[str, int]:
        """
        Логировать состояние таблиц после операции

        Args:
            title: Заголовок для логов
            created: Количество созданных записей
            updated: Количество обновленных записей
            skipped: Количество пропущенных записей

        Returns:
            Словарь {table_name: count}
        """
        self.after_counts = log_table_statistics(self.db, self.tables, title)

        # Логируем изменения для каждой таблицы
        logger.info("")
        logger.info("=" * 70)
        logger.info("CHANGES PER TABLE".center(70))
        logger.info("=" * 70)

        for table_name in self.tables:
            before = self.before_counts.get(table_name, 0)
            after = self.after_counts.get(table_name, 0)

            # Распределяем created/updated/skipped по таблицам
            # (если есть только одна таблица - используем все значения)
            if len(self.tables) == 1:
                log_table_change(table_name, before, after, created, updated, skipped)
            else:
                # Для множества таблиц показываем только delta
                log_table_change(table_name, before, after)

        logger.info("=" * 70)

        return self.after_counts

    def get_delta(self, table_name: str) -> int:
        """
        Получить изменение количества записей в таблице

        Args:
            table_name: Имя таблицы

        Returns:
            Разница в количестве записей (after - before)
        """
        before = self.before_counts.get(table_name, 0)
        after = self.after_counts.get(table_name, 0)
        return after - before

    def get_total_delta(self) -> int:
        """
        Получить общее изменение количества записей

        Returns:
            Сумма изменений по всем таблицам
        """
        return sum(self.get_delta(table) for table in self.tables)
