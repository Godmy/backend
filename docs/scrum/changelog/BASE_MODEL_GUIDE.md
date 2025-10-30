# BaseModel & Mixins - Полное руководство

## 📋 Содержание

- [Обзор](#обзор)
- [BaseModel - Основной класс](#basemodel---основной-класс)
- [Mixins - Дополнительная функциональность](#mixins---дополнительная-функциональность)
- [Примеры использования](#примеры-использования)
- [Миграция существующих моделей](#миграция-существующих-моделей)
- [Лучшие практики](#лучшие-практики)

---

## Обзор

`core/models/base.py` предоставляет модульную систему для создания моделей с различной функциональностью:

**BaseModel** - основной класс с базовыми полями (id, timestamps)

**Mixins** - опциональные модули для добавления функциональности:
- `SoftDeleteMixin` - мягкое удаление записей
- `VersionedMixin` - версионирование и отслеживание изменений
- `TenantMixin` - поддержка multi-tenancy
- `GDPRMixin` - GDPR compliance (анонимизация)
- `AuditMetadataMixin` - IP адреса и user agents
- `MetadataMixin` - произвольные JSON метаданные

**Готовые комбинации:**
- `FullAuditModel` - полный аудит (soft delete + versioning + metadata)
- `TenantAwareModel` - multi-tenant с soft delete

---

## BaseModel - Основной класс

### Поля

```python
class BaseModel(Base):
    id: int                    # Primary key
    created_at: DateTime       # Дата создания (UTC, timezone-aware)
    updated_at: DateTime       # Дата обновления (UTC, timezone-aware)
```

### Методы

```python
# Получить запись по ID
user = User.get_by_id(db, id=123)

# Получить все записи с пагинацией
users = User.get_all(db, limit=50, offset=0)

# Подсчитать записи
total = User.count(db)

# Сохранить
user.save(db)

# Удалить (hard delete)
user.delete(db)

# Преобразовать в словарь
data = user.to_dict()
```

### Пример

```python
from core.models.base import BaseModel
from sqlalchemy import Column, String

class Language(BaseModel):
    __tablename__ = "languages"

    code = Column(String(10), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
```

---

## Mixins - Дополнительная функциональность

### 1. SoftDeleteMixin - Мягкое удаление

**User Story:** #6 - Soft Delete для всех моделей (P2)

**Поля:**
- `deleted_at: DateTime` - когда удалено (NULL = активна)
- `deleted_by_id: int` - кто удалил
- `deleted_by: User` - relationship к пользователю

**Методы:**

```python
# Мягкое удаление
user.soft_delete(db, deleted_by_user_id=admin.id)

# Восстановление
user.restore(db)

# Проверка статуса
if user.is_deleted():
    print("Удалено")

# Запросы
active_users = User.active(db).all()           # Только активные
deleted_users = User.deleted(db).all()         # Только удаленные
all_users = User.with_deleted(db).all()        # Все
```

**Использование:**

```python
from core.models.base import BaseModel, SoftDeleteMixin

class User(SoftDeleteMixin, BaseModel):
    __tablename__ = "users"
    username = Column(String(100), unique=True)
    email = Column(String(255), unique=True)
```

**Автоматическая очистка старых записей:**

```python
# tasks/cleanup_tasks.py
from datetime import datetime, timedelta

@celery_app.task
def cleanup_old_deleted_records():
    """Удалить записи, удаленные более 90 дней назад"""
    cutoff_date = datetime.utcnow() - timedelta(days=90)

    db = next(get_db())
    old_deleted = db.query(User).filter(
        User.deleted_at < cutoff_date
    ).all()

    for user in old_deleted:
        db.delete(user)  # Hard delete

    db.commit()
```

---

### 2. VersionedMixin - Версионирование

**User Story:** #13 - Version History для концепций (P3)

**Поля:**
- `version: int` - номер версии (auto-increment)
- `content_hash: str` - SHA256 хэш контента

**Методы:**

```python
# Автоматически инкрементируется при update
concept.name = "New Name"
concept.save(db)  # version: 1 -> 2

# Проверить, были ли изменения
if concept.is_modified():
    print("Данные изменились с последнего сохранения")

# Вручную обновить хэш
concept.update_hash()

# Вручную инкрементировать версию
concept.increment_version()
```

**Использование:**

```python
from core.models.base import BaseModel, VersionedMixin

class Concept(VersionedMixin, BaseModel):
    __tablename__ = "concepts"

    name = Column(String(255), nullable=False)
    description = Column(Text)
    path = Column(String(500))
```

**Создание истории версий:**

```python
# languages/models/concept_version.py
class ConceptVersion(BaseModel):
    """История изменений концепций"""
    __tablename__ = "concept_versions"

    concept_id = Column(Integer, ForeignKey('concepts.id'))
    version = Column(Integer, nullable=False)
    data = Column(JSON, nullable=False)  # Снапшот данных
    changed_by_id = Column(Integer, ForeignKey('users.id'))

    # Индекс для быстрого поиска
    __table_args__ = (
        Index('idx_concept_version', 'concept_id', 'version'),
    )

# Service method
def save_version(db: Session, concept: Concept, changed_by_id: int):
    version = ConceptVersion(
        concept_id=concept.id,
        version=concept.version,
        data=concept.to_dict(),
        changed_by_id=changed_by_id
    )
    db.add(version)
    db.commit()
```

---

### 3. TenantMixin - Multi-Tenancy

**User Story:** #29 - Multi-Tenancy Support (P3)

**Поля:**
- `tenant_id: int` - ID организации
- `tenant: Organization` - relationship

**Методы:**

```python
# Запросить данные по tenant
tenant_users = User.by_tenant(db, tenant_id=123).all()
```

**Использование:**

```python
from core.models.base import TenantAwareModel

class Document(TenantAwareModel):
    __tablename__ = "documents"

    title = Column(String(255), nullable=False)
    content = Column(Text)
```

**Middleware для автоматической фильтрации:**

```python
# middleware/tenant.py
class TenantMiddleware:
    async def __call__(self, request, call_next):
        # Определить tenant из subdomain
        subdomain = request.url.hostname.split('.')[0]

        org = db.query(Organization).filter_by(subdomain=subdomain).first()
        if not org:
            return JSONResponse({"error": "Invalid tenant"}, status_code=400)

        request.state.tenant_id = org.id
        return await call_next(request)

# В GraphQL context
context['tenant_id'] = request.state.tenant_id

# В сервисах
def get_documents(db: Session, tenant_id: int):
    return Document.by_tenant(db, tenant_id).all()
```

---

### 4. GDPRMixin - GDPR Compliance

**User Story:** #40 - GDPR Compliance Tools (P2)

**Поля:**
- `is_anonymized: bool` - флаг анонимизации
- `anonymized_at: DateTime` - когда анонимизировано
- `anonymized_by_id: int` - кто анонимизировал
- `anonymized_by: User` - relationship

**Методы:**

```python
# Анонимизировать (только установить флаг)
user.anonymize(db, anonymized_by_user_id=admin.id)

# Полная анонимизация в сервисе
def anonymize_user(db: Session, user: User, admin_id: int):
    # Заменить персональные данные
    user.email = f"anonymized_{user.id}@deleted.local"
    user.username = f"user_{user.id}"
    user.first_name = "Deleted"
    user.last_name = "User"

    # Установить флаг
    user.anonymize(db, anonymized_by_user_id=admin_id)

    # Удалить связанные данные
    db.query(UserProfile).filter_by(user_id=user.id).delete()

    db.commit()
```

**Использование:**

```python
from core.models.base import BaseModel, GDPRMixin, SoftDeleteMixin

class User(GDPRMixin, SoftDeleteMixin, BaseModel):
    __tablename__ = "users"

    username = Column(String(100), unique=True)
    email = Column(String(255), unique=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
```

---

### 5. AuditMetadataMixin - Audit Metadata

**User Story:** #53 - API Request/Response Logging (P2)

**Поля:**
- `created_by_ip: str` - IP адрес создателя
- `created_by_user_agent: str` - User agent создателя
- `updated_by_ip: str` - IP адрес последнего обновления
- `updated_by_user_agent: str` - User agent обновления

**Использование:**

```python
from core.models.base import BaseModel, AuditMetadataMixin

class SensitiveDocument(AuditMetadataMixin, BaseModel):
    __tablename__ = "sensitive_documents"

    title = Column(String(255))
    content = Column(Text)

# В GraphQL mutation
def create_document(info: Info, input: CreateDocumentInput):
    request = info.context['request']

    doc = SensitiveDocument(
        title=input.title,
        content=input.content,
        created_by_ip=request.client.host,
        created_by_user_agent=request.headers.get('User-Agent')
    )

    doc.save(db)
    return doc
```

---

### 6. MetadataMixin - Generic Metadata

**Поля:**
- `metadata: JSON` - произвольные JSON данные

**Использование:**

```python
from core.models.base import BaseModel, MetadataMixin

class User(MetadataMixin, BaseModel):
    __tablename__ = "users"
    username = Column(String(100))

# Хранение настроек
user.metadata = {
    "preferences": {
        "theme": "dark",
        "language": "ru",
        "notifications": True
    },
    "onboarding_completed": True,
    "last_login_device": "iPhone 13"
}

# Обновление части метаданных
user.metadata['preferences']['theme'] = 'light'
flag_modified(user, 'metadata')  # Уведомить SQLAlchemy об изменении
db.commit()
```

---

## Примеры использования

## 📁 Project Structure

```
core/
└── models/
    ├── base.py                 # BaseModel (core functionality)
    └── mixins/                 # Optional mixins
        ├── __init__.py         # Exports all mixins
        ├── soft_delete.py      # SoftDeleteMixin
        ├── versioned.py        # VersionedMixin
        ├── tenant.py           # TenantMixin
        ├── gdpr.py             # GDPRMixin
        ├── audit_metadata.py   # AuditMetadataMixin
        ├── metadata.py         # MetadataMixin
        └── combinations.py     # Pre-configured combos
```

Each file has a **single responsibility** following SOLID principles.

---

### Простая модель

```python
from core.models.base import BaseModel

class Language(BaseModel):
    __tablename__ = "languages"

    code = Column(String(10), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
```

### Модель с soft delete

```python
from core.models.base import BaseModel
from core.models.mixins import SoftDeleteMixin

class Category(SoftDeleteMixin, BaseModel):
    __tablename__ = "categories"

    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)

# Использование
category.soft_delete(db, deleted_by_user_id=admin.id)
active_categories = Category.active(db).all()
```

### Модель с версионированием

```python
from core.models.base import BaseModel
from core.models.mixins import VersionedMixin, SoftDeleteMixin

class Concept(VersionedMixin, SoftDeleteMixin, BaseModel):
    __tablename__ = "concepts"

    name = Column(String(255), nullable=False)
    path = Column(String(500))
    description = Column(Text)

# Автоматический инкремент версии при update
concept.name = "Updated Name"
concept.save(db)  # version: 1 -> 2
```

### Multi-tenant модель

```python
from core.models.mixins import TenantAwareModel

class Project(TenantAwareModel):
    __tablename__ = "projects"

    name = Column(String(255), nullable=False)
    description = Column(Text)

# Запрос по tenant
projects = Project.by_tenant(db, tenant_id=request.state.tenant_id).all()
```

### Полный аудит

```python
from core.models.mixins import FullAuditModel

class Contract(FullAuditModel):
    """Контракт с полным аудитом всех действий"""
    __tablename__ = "contracts"

    contract_number = Column(String(50), unique=True)
    amount = Column(Numeric(12, 2))
    status = Column(String(20))

# Включает: soft delete, versioning, audit metadata, timestamps
```

### Кастомная комбинация

```python
from core.models.base import BaseModel
from core.models.mixins import (
    SoftDeleteMixin,
    VersionedMixin,
    TenantMixin,
    GDPRMixin,
    MetadataMixin
)

class UserProfile(
    TenantMixin,      # Multi-tenancy
    GDPRMixin,        # GDPR compliance
    SoftDeleteMixin,  # Soft delete
    MetadataMixin,    # Flexible metadata
    BaseModel
):
    __tablename__ = "user_profiles"

    user_id = Column(Integer, ForeignKey('users.id'))
    bio = Column(Text)
    avatar_url = Column(String(500))
```

---

## Миграция существующих моделей

### Шаг 1: Добавить mixin к модели

```python
# До
class User(BaseModel):
    __tablename__ = "users"
    username = Column(String(100))

# После
class User(SoftDeleteMixin, BaseModel):
    __tablename__ = "users"
    username = Column(String(100))
```

### Шаг 2: Создать миграцию

```bash
alembic revision --autogenerate -m "Add soft delete to users"
```

### Шаг 3: Проверить сгенерированную миграцию

```python
# migrations/versions/xxx_add_soft_delete_to_users.py
def upgrade():
    op.add_column('users', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('deleted_by_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_users_deleted_by', 'users', 'users', ['deleted_by_id'], ['id'], ondelete='SET NULL')
    op.create_index('ix_users_deleted_at', 'users', ['deleted_at'])

def downgrade():
    op.drop_index('ix_users_deleted_at', 'users')
    op.drop_constraint('fk_users_deleted_by', 'users', type_='foreignkey')
    op.drop_column('users', 'deleted_by_id')
    op.drop_column('users', 'deleted_at')
```

### Шаг 4: Применить миграцию

```bash
alembic upgrade head
```

### Шаг 5: Обновить код

```python
# До
users = db.query(User).all()

# После
users = User.active(db).all()  # Только активные
```

---

## Лучшие практики

### 1. Порядок Mixins имеет значение

```python
# ✅ Правильно: слева направо, от специфичного к базовому
class User(TenantMixin, SoftDeleteMixin, VersionedMixin, BaseModel):
    pass

# ❌ Неправильно: BaseModel должен быть последним
class User(BaseModel, SoftDeleteMixin):
    pass
```

### 2. Используйте готовые комбинации

```python
# ✅ Используйте готовые классы
class Document(FullAuditModel):
    pass

# ⚠️ Или создайте кастомную, если нужно
class Document(SoftDeleteMixin, VersionedMixin, BaseModel):
    pass
```

### 3. Индексы для производительности

```python
class User(SoftDeleteMixin, BaseModel):
    __tablename__ = "users"

    email = Column(String(255), unique=True)

    # Composite index для частых запросов
    __table_args__ = (
        Index('idx_active_users_email', 'email', 'deleted_at'),
    )
```

### 4. Всегда используйте .active() для soft delete моделей

```python
# ✅ Правильно
active_users = User.active(db).filter(User.email.like('%@gmail.com')).all()

# ❌ Неправильно (вернет и удаленные записи)
users = db.query(User).filter(User.email.like('%@gmail.com')).all()
```

### 5. Обработка версионирования в UI

```python
# GraphQL mutation с optimistic locking
@strawberry.mutation
def update_concept(
    info: Info,
    id: int,
    input: UpdateConceptInput,
    expected_version: int  # Клиент передает версию
) -> ConceptType:
    concept = db.query(Concept).filter_by(id=id).first()

    if concept.version != expected_version:
        raise GraphQLError(
            "Concept was modified by another user",
            extensions={"code": "CONCURRENT_MODIFICATION"}
        )

    concept.name = input.name
    concept.save(db)  # version auto-incremented

    return concept
```

### 6. Scheduled cleanup для soft delete

```python
# tasks/cleanup_tasks.py
@celery_app.task
def cleanup_old_deleted_records():
    """Permanent delete записей старше 90 дней"""
    from datetime import datetime, timedelta

    cutoff = datetime.utcnow() - timedelta(days=90)

    # Для каждой модели с SoftDeleteMixin
    for model in [User, Concept, Dictionary]:
        old_deleted = db.query(model).filter(
            model.deleted_at < cutoff
        ).all()

        for record in old_deleted:
            db.delete(record)  # Hard delete

    db.commit()

# Celery Beat schedule
celery_app.conf.beat_schedule['cleanup-deleted-records'] = {
    'task': 'tasks.cleanup_tasks.cleanup_old_deleted_records',
    'schedule': crontab(hour=3, minute=0, day_of_week=0),  # Каждое воскресенье в 3 AM
}
```

---

## Поддерживаемые User Stories

Этот файл поддерживает следующие задачи из BACKLOG.md:

- ✅ **#4** - Audit Logging System (Done)
- 📋 **#6** - Soft Delete для всех моделей (P2)
- 📋 **#13** - Version History для концепций (P3)
- 📋 **#29** - Multi-Tenancy Support (P3)
- 📋 **#40** - GDPR Compliance Tools (P2)
- 📋 **#53** - API Request/Response Logging (P2)

---

## Дополнительные ресурсы

- [SQLAlchemy Mixins Documentation](https://docs.sqlalchemy.org/en/14/orm/declarative_mixins.html)
- [BACKLOG.md](../BACKLOG.md) - Полный список задач
- [ARCHITECTURE.md](../ARCHITECTURE.md) - Архитектура проекта

---

**Обновлено:** 2025-01-19
