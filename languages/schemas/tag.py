import strawberry
from typing import List, Optional

from languages.models.tag import TagModel


@strawberry.type
class Tag:
    """GraphQL тип для тегов"""
    id: int
    name: str
    color: Optional[str] = None


@strawberry.input
class CreateTagInput:
    """Input для создания тега"""
    name: str
    color: Optional[str] = None


@strawberry.input
class UpdateTagInput:
    """Input для обновления тега"""
    id: int
    name: Optional[str] = None
    color: Optional[str] = None


@strawberry.input
class AddTagToConceptInput:
    """Input для добавления тега к концепции"""
    concept_id: int
    tag_id: int


@strawberry.input
class RemoveTagFromConceptInput:
    """Input для удаления тега от концепции"""
    concept_id: int
    tag_id: int


@strawberry.type
class TagMutationResult:
    """Результат мутации с тегами"""
    success: bool
    message: str
    tag: Optional[Tag] = None


@strawberry.type
class ConceptQuery:
    """Запросы, связанные с тегами концепций"""

    @strawberry.field
    def concept_tags(self, concept_id: int) -> List[Tag]:
        """Получить теги для конкретной концепции"""
        from core.platform.db.database import SessionLocal
        from languages.models.concept import ConceptModel

        with SessionLocal() as db:
            concept = db.query(ConceptModel).filter(ConceptModel.id == concept_id).first()
            if concept:
                return [Tag(id=tag.id, name=tag.name, color=tag.color) for tag in concept.tags]
            return []

    @strawberry.field
    def tags_by_name(self, name: str) -> List[Tag]:
        """Найти теги по названию (с поддержкой автозаполнения)"""
        from core.platform.db.database import SessionLocal
        from languages.models.tag import TagModel

        with SessionLocal() as db:
            tags = db.query(TagModel).filter(TagModel.name.contains(name)).all()
            return [Tag(id=tag.id, name=tag.name, color=tag.color) for tag in tags]

    @strawberry.field
    def all_tags(self) -> List[Tag]:
        """Получить все теги"""
        from core.platform.db.database import SessionLocal
        from languages.models.tag import TagModel

        with SessionLocal() as db:
            tags = db.query(TagModel).all()
            return [Tag(id=tag.id, name=tag.name, color=tag.color) for tag in tags if not tag.is_deleted]


@strawberry.type
class ConceptMutation:
    """Мутации, связанные с тегами концепций"""

    @strawberry.mutation
    def create_tag(self, input: CreateTagInput) -> TagMutationResult:
        """Создать новый тег"""
        from core.platform.db.database import SessionLocal
        from languages.models.tag import TagModel

        with SessionLocal() as db:
            # Проверяем, что тег с таким именем не существует
            existing_tag = db.query(TagModel).filter(TagModel.name == input.name).first()
            if existing_tag:
                return TagMutationResult(
                    success=False,
                    message=f"Tag with name '{input.name}' already exists"
                )

            tag = TagModel(name=input.name, color=input.color)
            db.add(tag)
            db.commit()
            db.refresh(tag)

            return TagMutationResult(
                success=True,
                message="Tag created successfully",
                tag=Tag(id=tag.id, name=tag.name, color=tag.color)
            )

    @strawberry.mutation
    def add_tag_to_concept(self, input: AddTagToConceptInput) -> TagMutationResult:
        """Добавить тег к концепции"""
        from core.platform.db.database import SessionLocal
        from languages.models.concept import ConceptModel
        from languages.models.tag import TagModel

        with SessionLocal() as db:
            concept = db.query(ConceptModel).filter(ConceptModel.id == input.concept_id).first()
            tag = db.query(TagModel).filter(TagModel.id == input.tag_id).first()

            if not concept:
                return TagMutationResult(
                    success=False,
                    message=f"Concept with id {input.concept_id} not found"
                )

            if not tag:
                return TagMutationResult(
                    success=False,
                    message=f"Tag with id {input.tag_id} not found"
                )

            # Проверяем, что тег не привязан к концепции уже
            if tag not in concept.tags:
                concept.tags.append(tag)
                db.commit()

            return TagMutationResult(
                success=True,
                message="Tag added to concept successfully"
            )

    @strawberry.mutation
    def remove_tag_from_concept(self, input: RemoveTagFromConceptInput) -> TagMutationResult:
        """Удалить тег из концепции"""
        from core.platform.db.database import SessionLocal
        from languages.models.concept import ConceptModel
        from languages.models.tag import TagModel

        with SessionLocal() as db:
            concept = db.query(ConceptModel).filter(ConceptModel.id == input.concept_id).first()
            tag = db.query(TagModel).filter(TagModel.id == input.tag_id).first()

            if not concept:
                return TagMutationResult(
                    success=False,
                    message=f"Concept with id {input.concept_id} not found"
                )

            if not tag:
                return TagMutationResult(
                    success=False,
                    message=f"Tag with id {input.tag_id} not found"
                )

            # Проверяем, что тег привязан к концепции
            if tag in concept.tags:
                concept.tags.remove(tag)
                db.commit()

            return TagMutationResult(
                success=True,
                message="Tag removed from concept successfully"
            )

    @strawberry.mutation
    def delete_tag(self, tag_id: int) -> TagMutationResult:
        """Удалить тег (мягкое удаление)"""
        from core.platform.db.database import SessionLocal
        from languages.models.tag import TagModel

        with SessionLocal() as db:
            tag = db.query(TagModel).filter(TagModel.id == tag_id).first()

            if not tag:
                return TagMutationResult(
                    success=False,
                    message=f"Tag with id {tag_id} not found"
                )

            # Мягкое удаление
            tag.is_deleted = True
            db.commit()

            return TagMutationResult(
                success=True,
                message="Tag deleted successfully"
            )