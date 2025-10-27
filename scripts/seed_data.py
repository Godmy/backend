"""
Скрипт для инициализации тестовых данных в базе
Создает полноценный набор данных для тестирования и демонстрации функциональности
"""

import os
import sys
from datetime import datetime

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging

from auth.models import PermissionModel, RoleModel, UserModel, UserRoleModel
from auth.models.profile import UserProfileModel
from auth.utils.security import hash_password
from core.database import SessionLocal
from languages.models import ConceptModel, DictionaryModel, LanguageModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_languages(db):
    """Добавить базовые языки"""
    # Проверяем, есть ли уже данные
    existing = db.query(LanguageModel).first()
    if existing:
        logger.info("Languages already exist, skipping...")
        return

    languages = [
        LanguageModel(code="ru", name="Русский"),
        LanguageModel(code="en", name="English"),
        LanguageModel(code="es", name="Español"),
        LanguageModel(code="fr", name="Français"),
        LanguageModel(code="de", name="Deutsch"),
        LanguageModel(code="zh", name="中文"),
        LanguageModel(code="ja", name="日本語"),
        LanguageModel(code="ar", name="العربية"),
    ]

    db.add_all(languages)
    db.commit()
    logger.info(f"✓ Added {len(languages)} languages")


def seed_permissions_and_roles(db):
    """Создать систему разрешений и ролей"""
    # Проверяем, есть ли уже роли
    existing = db.query(RoleModel).first()
    if existing:
        logger.info("Roles already exist, skipping...")
        return

    # Создаем роли
    roles = [
        RoleModel(name="guest", description="Guest user - read-only access to public content"),
        RoleModel(name="user", description="Regular user - can view and create own content"),
        RoleModel(name="editor", description="Editor - can manage content and translations"),
        RoleModel(name="moderator", description="Moderator - can manage users and review content"),
        RoleModel(name="admin", description="Administrator - full system access"),
    ]

    db.add_all(roles)
    db.flush()

    # Получаем созданные роли
    role_dict = {r.name: r for r in roles}

    # Создаем права доступа для каждой роли
    # PermissionModel(role_id, resource, action, scope)

    permissions = []

    # Guest - только чтение
    guest_permissions = [
        PermissionModel(
            role_id=role_dict["guest"].id, resource="concepts", action="read", scope="all"
        ),
        PermissionModel(
            role_id=role_dict["guest"].id, resource="dictionaries", action="read", scope="all"
        ),
        PermissionModel(
            role_id=role_dict["guest"].id, resource="languages", action="read", scope="all"
        ),
    ]
    permissions.extend(guest_permissions)

    # User - чтение + создание своего контента
    user_permissions = [
        PermissionModel(
            role_id=role_dict["user"].id, resource="concepts", action="read", scope="all"
        ),
        PermissionModel(
            role_id=role_dict["user"].id, resource="concepts", action="create", scope="own"
        ),
        PermissionModel(
            role_id=role_dict["user"].id, resource="dictionaries", action="read", scope="all"
        ),
        PermissionModel(
            role_id=role_dict["user"].id, resource="dictionaries", action="create", scope="own"
        ),
        PermissionModel(
            role_id=role_dict["user"].id, resource="languages", action="read", scope="all"
        ),
    ]
    permissions.extend(user_permissions)

    # Editor - управление всем контентом
    editor_permissions = [
        PermissionModel(
            role_id=role_dict["editor"].id, resource="concepts", action="read", scope="all"
        ),
        PermissionModel(
            role_id=role_dict["editor"].id, resource="concepts", action="create", scope="all"
        ),
        PermissionModel(
            role_id=role_dict["editor"].id, resource="concepts", action="update", scope="all"
        ),
        PermissionModel(
            role_id=role_dict["editor"].id, resource="concepts", action="delete", scope="all"
        ),
        PermissionModel(
            role_id=role_dict["editor"].id, resource="dictionaries", action="read", scope="all"
        ),
        PermissionModel(
            role_id=role_dict["editor"].id, resource="dictionaries", action="create", scope="all"
        ),
        PermissionModel(
            role_id=role_dict["editor"].id, resource="dictionaries", action="update", scope="all"
        ),
        PermissionModel(
            role_id=role_dict["editor"].id, resource="dictionaries", action="delete", scope="all"
        ),
        PermissionModel(
            role_id=role_dict["editor"].id, resource="languages", action="read", scope="all"
        ),
        PermissionModel(
            role_id=role_dict["editor"].id, resource="languages", action="create", scope="all"
        ),
        PermissionModel(
            role_id=role_dict["editor"].id, resource="languages", action="update", scope="all"
        ),
    ]
    permissions.extend(editor_permissions)

    # Moderator - + управление пользователями
    moderator_permissions = editor_permissions + [
        PermissionModel(
            role_id=role_dict["moderator"].id, resource="users", action="read", scope="all"
        ),
        PermissionModel(
            role_id=role_dict["moderator"].id, resource="users", action="update", scope="all"
        ),
        PermissionModel(
            role_id=role_dict["moderator"].id, resource="users", action="delete", scope="all"
        ),
    ]
    permissions.extend(moderator_permissions)

    # Admin - полный доступ ко всему
    admin_permissions = [
        PermissionModel(role_id=role_dict["admin"].id, resource="*", action="*", scope="all"),
    ]
    permissions.extend(admin_permissions)

    db.add_all(permissions)
    db.commit()

    logger.info(f"✓ Added {len(roles)} roles with {len(permissions)} permissions")


def seed_users(db):
    """Создать тестовых пользователей"""
    # Проверяем, есть ли уже пользователи
    existing = db.query(UserModel).first()
    if existing:
        logger.info("Users already exist, skipping...")
        return

    # Получаем роли
    roles = {r.name: r for r in db.query(RoleModel).all()}

    # Создаем тестовых пользователей
    users_data = [
        {
            "username": "admin",
            "email": "admin@multipult.dev",
            "password": "Admin123!",
            "is_active": True,
            "is_verified": True,
            "role": "admin",
            "profile": {
                "first_name": "Администратор",
                "last_name": "Системы",
                "bio": "Главный администратор системы МультиПУЛЬТ",
            },
        },
        {
            "username": "moderator",
            "email": "moderator@multipult.dev",
            "password": "Moderator123!",
            "is_active": True,
            "is_verified": True,
            "role": "moderator",
            "profile": {
                "first_name": "Модератор",
                "last_name": "Контента",
                "bio": "Модератор и проверяющий контент",
            },
        },
        {
            "username": "editor",
            "email": "editor@multipult.dev",
            "password": "Editor123!",
            "is_active": True,
            "is_verified": True,
            "role": "editor",
            "profile": {
                "first_name": "Редактор",
                "last_name": "Словарей",
                "bio": "Редактор переводов и концепций",
            },
        },
        {
            "username": "testuser",
            "email": "user@multipult.dev",
            "password": "User123!",
            "is_active": True,
            "is_verified": True,
            "role": "user",
            "profile": {
                "first_name": "Тестовый",
                "last_name": "Пользователь",
                "bio": "Обычный пользователь системы",
            },
        },
        {
            "username": "john_doe",
            "email": "john.doe@example.com",
            "password": "John123!",
            "is_active": True,
            "is_verified": False,
            "role": "user",
            "profile": {
                "first_name": "John",
                "last_name": "Doe",
                "bio": "Learning multiple languages",
            },
        },
    ]

    for user_data in users_data:
        # Создаем пользователя
        user = UserModel(
            username=user_data["username"],
            email=user_data["email"],
            password_hash=hash_password(user_data["password"]),
            is_active=user_data["is_active"],
            is_verified=user_data["is_verified"],
        )
        db.add(user)
        db.flush()

        # Создаем профиль
        profile = UserProfileModel(
            user_id=user.id,
            first_name=user_data["profile"]["first_name"],
            last_name=user_data["profile"]["last_name"],
            bio=user_data["profile"]["bio"],
        )
        db.add(profile)

        # Назначаем роль
        role = roles[user_data["role"]]
        user_role = UserRoleModel(user_id=user.id, role_id=role.id)
        db.add(user_role)

    db.commit()
    logger.info(f"✓ Added {len(users_data)} test users")
    logger.info("  Login credentials:")
    for user_data in users_data:
        logger.info(f"    {user_data['username']} / {user_data['password']} ({user_data['role']})")


def seed_concepts(db):
    """Создать иерархию концепций"""
    # Проверяем, есть ли уже концепции
    existing = db.query(ConceptModel).first()
    if existing:
        logger.info("Concepts already exist, skipping...")
        return

    # Корневые концепции (категории верхнего уровня)
    root_concepts = [
        {"path": "colors", "depth": 0},
        {"path": "animals", "depth": 0},
        {"path": "food", "depth": 0},
        {"path": "emotions", "depth": 0},
        {"path": "numbers", "depth": 0},
        {"path": "family", "depth": 0},
        {"path": "time", "depth": 0},
        {"path": "weather", "depth": 0},
    ]

    concepts = []
    for concept_data in root_concepts:
        concept = ConceptModel(
            path=concept_data["path"], depth=concept_data["depth"], parent_id=None
        )
        db.add(concept)
        concepts.append(concept)

    db.flush()

    # Создаем концепции второго уровня
    # Цвета
    colors_parent = next(c for c in concepts if c.path == "colors")
    color_names = ["red", "blue", "green", "yellow", "black", "white", "orange", "purple"]
    for color in color_names:
        concept = ConceptModel(path=f"colors.{color}", depth=1, parent_id=colors_parent.id)
        db.add(concept)

    # Животные
    animals_parent = next(c for c in concepts if c.path == "animals")
    animal_categories = ["mammals", "birds", "fish", "insects", "reptiles"]
    for category in animal_categories:
        concept = ConceptModel(path=f"animals.{category}", depth=1, parent_id=animals_parent.id)
        db.add(concept)

    db.flush()

    # Млекопитающие (третий уровень)
    mammals = db.query(ConceptModel).filter_by(path="animals.mammals").first()
    mammal_names = ["cat", "dog", "elephant", "lion", "bear", "horse"]
    for mammal in mammal_names:
        concept = ConceptModel(path=f"animals.mammals.{mammal}", depth=2, parent_id=mammals.id)
        db.add(concept)

    # Еда
    food_parent = next(c for c in concepts if c.path == "food")
    food_categories = ["fruits", "vegetables", "meat", "dairy", "grains"]
    for category in food_categories:
        concept = ConceptModel(path=f"food.{category}", depth=1, parent_id=food_parent.id)
        db.add(concept)

    db.flush()

    # Фрукты
    fruits = db.query(ConceptModel).filter_by(path="food.fruits").first()
    fruit_names = ["apple", "banana", "orange", "grape", "strawberry"]
    for fruit in fruit_names:
        concept = ConceptModel(path=f"food.fruits.{fruit}", depth=2, parent_id=fruits.id)
        db.add(concept)

    # Эмоции
    emotions_parent = next(c for c in concepts if c.path == "emotions")
    emotion_names = ["happy", "sad", "angry", "afraid", "surprised", "love"]
    for emotion in emotion_names:
        concept = ConceptModel(path=f"emotions.{emotion}", depth=1, parent_id=emotions_parent.id)
        db.add(concept)

    # Числа
    numbers_parent = next(c for c in concepts if c.path == "numbers")
    for i in range(1, 11):
        concept = ConceptModel(path=f"numbers.{i}", depth=1, parent_id=numbers_parent.id)
        db.add(concept)

    # Семья
    family_parent = next(c for c in concepts if c.path == "family")
    family_members = [
        "father",
        "mother",
        "brother",
        "sister",
        "son",
        "daughter",
        "grandfather",
        "grandmother",
        "uncle",
        "aunt",
    ]
    for member in family_members:
        concept = ConceptModel(path=f"family.{member}", depth=1, parent_id=family_parent.id)
        db.add(concept)

    db.commit()

    total_concepts = db.query(ConceptModel).count()
    logger.info(f"✓ Added {total_concepts} concepts in hierarchical structure")


def seed_dictionaries(db):
    """Создать переводы для концепций"""
    # Проверяем, есть ли уже словари
    existing = db.query(DictionaryModel).first()
    if existing:
        logger.info("Dictionaries already exist, skipping...")
        return

    # Получаем языки
    languages = {lang.code: lang for lang in db.query(LanguageModel).all()}

    # Словарь переводов (концепция -> {язык: перевод})
    translations = {
        # Цвета
        "colors": {
            "ru": "Цвета",
            "en": "Colors",
            "es": "Colores",
            "de": "Farben",
            "fr": "Couleurs",
        },
        "colors.red": {"ru": "Красный", "en": "Red", "es": "Rojo", "de": "Rot", "fr": "Rouge"},
        "colors.blue": {"ru": "Синий", "en": "Blue", "es": "Azul", "de": "Blau", "fr": "Bleu"},
        "colors.green": {"ru": "Зелёный", "en": "Green", "es": "Verde", "de": "Grün", "fr": "Vert"},
        "colors.yellow": {
            "ru": "Жёлтый",
            "en": "Yellow",
            "es": "Amarillo",
            "de": "Gelb",
            "fr": "Jaune",
        },
        "colors.black": {
            "ru": "Чёрный",
            "en": "Black",
            "es": "Negro",
            "de": "Schwarz",
            "fr": "Noir",
        },
        "colors.white": {"ru": "Белый", "en": "White", "es": "Blanco", "de": "Weiß", "fr": "Blanc"},
        # Животные
        "animals": {
            "ru": "Животные",
            "en": "Animals",
            "es": "Animales",
            "de": "Tiere",
            "fr": "Animaux",
        },
        "animals.mammals": {
            "ru": "Млекопитающие",
            "en": "Mammals",
            "es": "Mamíferos",
            "de": "Säugetiere",
            "fr": "Mammifères",
        },
        "animals.mammals.cat": {
            "ru": "Кошка",
            "en": "Cat",
            "es": "Gato",
            "de": "Katze",
            "fr": "Chat",
        },
        "animals.mammals.dog": {
            "ru": "Собака",
            "en": "Dog",
            "es": "Perro",
            "de": "Hund",
            "fr": "Chien",
        },
        "animals.mammals.elephant": {
            "ru": "Слон",
            "en": "Elephant",
            "es": "Elefante",
            "de": "Elefant",
            "fr": "Éléphant",
        },
        "animals.mammals.lion": {
            "ru": "Лев",
            "en": "Lion",
            "es": "León",
            "de": "Löwe",
            "fr": "Lion",
        },
        # Еда
        "food": {"ru": "Еда", "en": "Food", "es": "Comida", "de": "Essen", "fr": "Nourriture"},
        "food.fruits": {
            "ru": "Фрукты",
            "en": "Fruits",
            "es": "Frutas",
            "de": "Früchte",
            "fr": "Fruits",
        },
        "food.fruits.apple": {
            "ru": "Яблоко",
            "en": "Apple",
            "es": "Manzana",
            "de": "Apfel",
            "fr": "Pomme",
        },
        "food.fruits.banana": {
            "ru": "Банан",
            "en": "Banana",
            "es": "Plátano",
            "de": "Banane",
            "fr": "Banane",
        },
        "food.fruits.orange": {
            "ru": "Апельсин",
            "en": "Orange",
            "es": "Naranja",
            "de": "Orange",
            "fr": "Orange",
        },
        # Эмоции
        "emotions": {
            "ru": "Эмоции",
            "en": "Emotions",
            "es": "Emociones",
            "de": "Emotionen",
            "fr": "Émotions",
        },
        "emotions.happy": {
            "ru": "Счастливый",
            "en": "Happy",
            "es": "Feliz",
            "de": "Glücklich",
            "fr": "Heureux",
        },
        "emotions.sad": {
            "ru": "Грустный",
            "en": "Sad",
            "es": "Triste",
            "de": "Traurig",
            "fr": "Triste",
        },
        "emotions.angry": {
            "ru": "Злой",
            "en": "Angry",
            "es": "Enfadado",
            "de": "Wütend",
            "fr": "En colère",
        },
        "emotions.love": {"ru": "Любовь", "en": "Love", "es": "Amor", "de": "Liebe", "fr": "Amour"},
        # Числа
        "numbers": {
            "ru": "Числа",
            "en": "Numbers",
            "es": "Números",
            "de": "Zahlen",
            "fr": "Nombres",
        },
        "numbers.1": {"ru": "Один", "en": "One", "es": "Uno", "de": "Eins", "fr": "Un"},
        "numbers.2": {"ru": "Два", "en": "Two", "es": "Dos", "de": "Zwei", "fr": "Deux"},
        "numbers.3": {"ru": "Три", "en": "Three", "es": "Tres", "de": "Drei", "fr": "Trois"},
        "numbers.5": {"ru": "Пять", "en": "Five", "es": "Cinco", "de": "Fünf", "fr": "Cinq"},
        "numbers.10": {"ru": "Десять", "en": "Ten", "es": "Diez", "de": "Zehn", "fr": "Dix"},
        # Семья
        "family": {
            "ru": "Семья",
            "en": "Family",
            "es": "Familia",
            "de": "Familie",
            "fr": "Famille",
        },
        "family.father": {"ru": "Отец", "en": "Father", "es": "Padre", "de": "Vater", "fr": "Père"},
        "family.mother": {
            "ru": "Мать",
            "en": "Mother",
            "es": "Madre",
            "de": "Mutter",
            "fr": "Mère",
        },
        "family.brother": {
            "ru": "Брат",
            "en": "Brother",
            "es": "Hermano",
            "de": "Bruder",
            "fr": "Frère",
        },
        "family.sister": {
            "ru": "Сестра",
            "en": "Sister",
            "es": "Hermana",
            "de": "Schwester",
            "fr": "Sœur",
        },
    }

    # Создаем словарные записи
    count = 0
    for concept_path, lang_translations in translations.items():
        # Находим концепцию
        concept = db.query(ConceptModel).filter_by(path=concept_path).first()
        if not concept:
            continue

        # Создаем перевод для каждого языка
        for lang_code, translation in lang_translations.items():
            if lang_code in languages:
                dictionary = DictionaryModel(
                    concept_id=concept.id,
                    language_id=languages[lang_code].id,
                    name=translation,
                    description=f"Translation of '{concept_path}' to {lang_code}",
                )
                db.add(dictionary)
                count += 1

    db.commit()
    logger.info(f"✓ Added {count} dictionary translations")


# def seed_ui_concepts(db):
#     """Импортировать и запустить seed UI-переводов"""
#     from scripts.seed_ui_concepts import seed_ui_concepts as seed_ui
#     seed_ui(db)


# def seed_domain_concepts(db):
#     """Импортировать и запустить seed доменных концепций"""
#     from scripts.seed_domain_concepts import seed_domain_concepts as seed_domain
#     seed_domain(db)


def seed_new_system(db):
    """
    Использовать новую модульную систему сидеров
    РЕКОМЕНДУЕТСЯ: более быстрая, модульная, оптимизированная
    """
    from scripts.seeders.orchestrator import SeederOrchestrator

    logger.info("=" * 60)
    logger.info("Using NEW modular seeder system")
    logger.info("=" * 60)

    orchestrator = SeederOrchestrator(db)
    results = orchestrator.run_all(skip_if_exists=True)

    # Проверка результатов
    failed = sum(1 for r in results if r.status == "failed")
    if failed > 0:
        raise Exception(f"Seeding failed: {failed} seeders encountered errors")


def main():
    """
    Запуск всех seed функций

    НОВАЯ СИСТЕМА (рекомендуется):
    - Использует модульную архитектуру по принципам SOLID
    - Оптимизирована для больших объемов данных
    - Автоматическое разрешение зависимостей
    - 10x быстрее для доменных концептов

    Для использования ТОЛЬКО новой системы:
        python scripts/seed_data_new.py
    """
    import time
    from core.db_stats import log_table_statistics

    start_time = time.time()

    logger.info("=" * 70)
    logger.info("STARTING DATABASE SEEDING".center(70))
    logger.info("=" * 70)

    db = SessionLocal()
    try:
        # Показываем статистику ДО seeding
        logger.info("")
        log_table_statistics(db, title="Database State BEFORE Seeding")
        logger.info("")

        # ВАРИАНТ 1: Новая модульная система (РЕКОМЕНДУЕТСЯ)
        seed_new_system(db)

        # ВАРИАНТ 2: Старая система (deprecated, оставлена для совместимости)
        # seed_languages(db)
        # seed_permissions_and_roles(db)
        # seed_users(db)
        # seed_concepts(db)
        # seed_dictionaries(db)
        # seed_ui_concepts(db)

        # Показываем статистику ПОСЛЕ seeding
        logger.info("")
        log_table_statistics(db, title="Database State AFTER Seeding")

        # Время выполнения
        duration = time.time() - start_time

        logger.info("")
        logger.info("=" * 70)
        logger.info("SEEDING PERFORMANCE".center(70))
        logger.info("=" * 70)
        logger.info(f"Total time: {duration:.2f} seconds")

        # Подсчет записей для скорости
        total_records = (
            db.query(LanguageModel).count()
            + db.query(UserModel).count()
            + db.query(RoleModel).count()
            + db.query(PermissionModel).count()
            + db.query(ConceptModel).count()
            + db.query(DictionaryModel).count()
        )

        if duration > 0:
            rate = total_records / duration
            logger.info(f"Speed: {rate:,.0f} records/second")

        logger.info("")
        logger.info("=" * 70)
        logger.info("✓ DATABASE SEEDING COMPLETED SUCCESSFULLY!".center(70))
        logger.info("=" * 70)

    except Exception as e:
        logger.error("")
        logger.error("=" * 70)
        logger.error("✗ SEEDING FAILED".center(70))
        logger.error("=" * 70)
        logger.error(f"Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
