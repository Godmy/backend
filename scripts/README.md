# Scripts Directory

Эта директория содержит утилиты и скрипты для инициализации и обслуживания проекта.

## Доступные скрипты

### seed_data.py

Скрипт для заполнения базы данных тестовыми данными.

**Что создается:**

1. **Языки (8 штук)**
   - Русский (ru)
   - English (en)
   - Español (es)
   - Français (fr)
   - Deutsch (de)
   - 中文 (zh)
   - 日本語 (ja)
   - العربية (ar)

2. **Система разрешений и ролей**

   **Разрешения (12 штук):**
   - `read` - Чтение ресурсов
   - `write` - Создание и обновление
   - `delete` - Удаление
   - `users.manage` - Управление пользователями
   - `users.view` - Просмотр информации о пользователях
   - `roles.manage` - Управление ролями и правами
   - `languages.manage` - Управление языками
   - `concepts.manage` - Управление иерархией концепций
   - `concepts.view` - Просмотр концепций
   - `dictionaries.manage` - Управление словарными записями
   - `dictionaries.view` - Просмотр словарных записей
   - `admin.full` - Полный административный доступ

   **Роли (5 штук):**
   - `guest` - Гость (только чтение публичного контента)
   - `user` - Обычный пользователь (может создавать свой контент)
   - `editor` - Редактор (управление контентом и переводами)
   - `moderator` - Модератор (управление пользователями)
   - `admin` - Администратор (полный доступ)

3. **Тестовые пользователи (5 штук)**

   | Username   | Email                    | Password       | Role      | Verified |
   |------------|--------------------------|----------------|-----------|----------|
   | admin      | admin@multipult.dev      | Admin123!      | admin     | ✓        |
   | moderator  | moderator@multipult.dev  | Moderator123!  | moderator | ✓        |
   | editor     | editor@multipult.dev     | Editor123!     | editor    | ✓        |
   | testuser   | user@multipult.dev       | User123!       | user      | ✓        |
   | john_doe   | john.doe@example.com     | John123!       | user      | ✗        |

   **Примечание:** Все пароли захешированы с использованием bcrypt.

4. **Иерархия концепций (~80 концепций)**

   **Корневые категории:**
   - `colors` - Цвета (red, blue, green, yellow, black, white, orange, purple)
   - `animals` - Животные
     - `mammals` - Млекопитающие (cat, dog, elephant, lion, bear, horse)
     - `birds` - Птицы
     - `fish` - Рыбы
     - `insects` - Насекомые
     - `reptiles` - Рептилии
   - `food` - Еда
     - `fruits` - Фрукты (apple, banana, orange, grape, strawberry)
     - `vegetables` - Овощи
     - `meat` - Мясо
     - `dairy` - Молочные продукты
     - `grains` - Зерновые
   - `emotions` - Эмоции (happy, sad, angry, afraid, surprised, love)
   - `numbers` - Числа (1-10)
   - `family` - Семья (father, mother, brother, sister, son, daughter, grandfather, grandmother, uncle, aunt)
   - `time` - Время
   - `weather` - Погода

5. **Словарные переводы (~150 записей)**

   Переводы на 5 языков (ru, en, es, de, fr) для основных концепций:
   - Все цвета
   - Базовые животные
   - Популярные фрукты
   - Основные эмоции
   - Числа
   - Члены семьи

## Использование

### Автоматический запуск при старте приложения

По умолчанию скрипт запускается автоматически при старте приложения, если установлена переменная окружения:

```bash
SEED_DATABASE=true
```

Для отключения автоматического заполнения (например, в production):

```bash
SEED_DATABASE=false
```

### Ручной запуск

Из корневой директории проекта:

```bash
python scripts/seed_data.py
```

Или через Docker:

```bash
docker-compose exec app python scripts/seed_data.py
```

## Особенности

- **Идемпотентность**: Скрипт можно запускать многократно - он проверяет существование данных и не создает дубликаты
- **Транзакции**: Все операции выполняются в транзакциях с откатом при ошибках
- **Логирование**: Подробное логирование всех операций
- **Валидация**: Пароли хешируются, проверяется целостность связей

## Расширение тестовых данных

Чтобы добавить новые тестовые данные:

1. Создайте новую функцию `seed_*` в `seed_data.py`
2. Добавьте вызов функции в `main()`
3. Следуйте паттерну: проверка существования → создание → коммит

Пример:

```python
def seed_categories(db):
    """Добавить категории"""
    existing = db.query(CategoryModel).first()
    if existing:
        logger.info("Categories already exist, skipping...")
        return

    categories = [
        CategoryModel(name="Category 1", description="Description 1"),
        CategoryModel(name="Category 2", description="Description 2"),
    ]

    db.add_all(categories)
    db.commit()
    logger.info(f"✓ Added {len(categories)} categories")
```

## Production considerations

В production окружении:

1. Установите `SEED_DATABASE=false` в `.env`
2. Используйте отдельный процесс миграции вместо seed
3. Не используйте тестовые пароли
4. Создавайте реальных пользователей через admin-панель или специальные скрипты

## Troubleshooting

**Проблема**: Скрипт выдает ошибку "already exists"
- **Решение**: Это нормально - данные уже созданы

**Проблема**: Import errors
- **Решение**: Убедитесь, что запускаете из корневой директории проекта

**Проблема**: Database connection errors
- **Решение**: Проверьте настройки подключения к БД в `.env`
