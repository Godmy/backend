"""
GraphQL schemas for managing dictionary entries, which are the translations of concepts.
"""

from typing import List, Optional, TYPE_CHECKING, Any
import strawberry

if TYPE_CHECKING:
    from languages.schemas.concept import Concept

# ============================================================================
# Types
# ============================================================================

@strawberry.type(description="Represents a dictionary entry, which is a translation of a concept in a specific language.")
class Dictionary:
    id: int = strawberry.field(description="Unique identifier for the dictionary entry.")
    concept_id: int = strawberry.field(description="The ID of the associated concept.")
    language_id: int = strawberry.field(description="The ID of the associated language.")
    name: str = strawberry.field(description="The name of the concept in this language.")
    description: Optional[str] = strawberry.field(description="A detailed description in this language.")
    image: Optional[str] = strawberry.field(description="URL for an image representing the concept in this language.")

    # Private field to hold the preloaded SQLAlchemy model
    concept_model: strawberry.Private[Optional[Any]] = None

    @strawberry.field(description="The concept this dictionary entry belongs to.")
    def concept(self) -> Optional[strawberry.LazyType["Concept", "languages.schemas.concept"]]:
        from languages.schemas.concept import Concept
        if not self.concept_model:
            return None
        # Map the SQLAlchemy model to the GraphQL type
        return Concept(
            id=self.concept_model.id,
            parent_id=self.concept_model.parent_id,
            path=self.concept_model.path,
            depth=self.concept_model.depth,
        )

# ============================================================================
# Inputs
# ============================================================================

@strawberry.input(description="Input for creating a new dictionary entry (translation).")
class DictionaryInput:
    concept_id: int = strawberry.field(description="The ID of the concept to translate.")
    language_id: int = strawberry.field(description="The ID of the language for this translation.")
    name: str = strawberry.field(description="The name/translation of the concept.")
    description: Optional[str] = strawberry.field(default=None, description="An optional description.")
    image: Optional[str] = strawberry.field(default=None, description="An optional image URL.")

@strawberry.input(description="Input for updating an existing dictionary entry.")
class DictionaryUpdateInput:
    name: Optional[str] = strawberry.field(default=None, description="The new name/translation.")
    description: Optional[str] = strawberry.field(default=None, description="The new description.")
    image: Optional[str] = strawberry.field(default=None, description="The new image URL.")
    concept_id: Optional[int] = strawberry.field(default=None, description="The new concept ID.")
    language_id: Optional[int] = strawberry.field(default=None, description="The new language ID.")

# ============================================================================
# Queries
# ============================================================================

@strawberry.type
class DictionaryQuery:
    """GraphQL queries for retrieving dictionary entries (translations)."""

    @strawberry.field(description="""Get a list of dictionary entries, with optional filtering by concept or language.

Example (get all translations for concept 10):
```graphql
query GetTranslationsForConcept {
  dictionaries(conceptId: 10) {
    id
    name
    language_id
  }
}
```
""")
    def dictionaries(
        self, info: strawberry.Info, concept_id: Optional[int] = None, language_id: Optional[int] = None
    ) -> List[Dictionary]:
        from languages.services.dictionary_service import DictionaryService
        db = info.context["db"]
        service = DictionaryService(db)

        if concept_id and language_id:
            items = service.get_by_concept_and_language(concept_id, language_id)
        elif concept_id:
            items = service.get_by_concept(concept_id)
        elif language_id:
            items = service.get_by_language(language_id)
        else:
            items = service.get_all()

        return [self._map_dict_to_gql(d) for d in items]

    @strawberry.field(description="Get a single dictionary entry by its unique ID.")
    def dictionary(self, info: strawberry.Info, dictionary_id: int) -> Optional[Dictionary]:
        from languages.services.dictionary_service import DictionaryService
        db = info.context["db"]
        service = DictionaryService(db)
        item = service.get_by_id(dictionary_id)
        return self._map_dict_to_gql(item) if item else None

    def _map_dict_to_gql(self, item_db) -> Dictionary:
        # Handle both model objects and dicts (from cache)
        if isinstance(item_db, dict):
            return Dictionary(
                id=item_db.get("id"),
                concept_id=item_db.get("concept_id"),
                language_id=item_db.get("language_id"),
                name=item_db.get("name"),
                description=item_db.get("description"),
                image=item_db.get("image"),
            )
        return Dictionary(
            id=item_db.id,
            concept_id=item_db.concept_id,
            language_id=item_db.language_id,
            name=item_db.name,
            description=item_db.description,
            image=item_db.image,
            concept_model=item_db.concept  # Pass preloaded concept model
        )

# ============================================================================
# Mutations
# ============================================================================

@strawberry.type
class DictionaryMutation:
    """GraphQL mutations for managing dictionary entries (translations)."""

    @strawberry.mutation(description="""Create a new dictionary entry (translation) for a concept.

A concept can only have one translation per language.

Example:
```graphql
mutation CreateTranslation {
  createDictionary(input: {
    conceptId: 10
    languageId: 1
    name: "Красный"
    description: "Цвет крови и огня"
  }) {
    id
    name
    concept {
      path
    }
  }
}
```
""")
    def create_dictionary(self, info: strawberry.Info, input: DictionaryInput) -> Dictionary:
        from languages.services.dictionary_service import DictionaryService
        db = info.context["db"]
        service = DictionaryService(db)
        item = service.create(**input.__dict__)
        return DictionaryQuery._map_dict_to_gql(self, item)

    @strawberry.mutation(description="""Update an existing dictionary entry.

Example:
```graphql
mutation UpdateTranslation {
  updateDictionary(dictionaryId: 1, input: { name: "Алый" }) {
    id
    name
  }
}
```
""")
    def update_dictionary(self, info: strawberry.Info, dictionary_id: int, input: DictionaryUpdateInput) -> Dictionary:
        from languages.services.dictionary_service import DictionaryService
        db = info.context["db"]
        service = DictionaryService(db)
        item = service.update(dictionary_id, **input.__dict__)
        if not item:
            raise Exception("Dictionary entry not found")
        return DictionaryQuery._map_dict_to_gql(self, item)

    @strawberry.mutation(description="""Soft delete a dictionary entry. This is a reversible action.

Example:
```graphql
mutation DeleteTranslation {
  deleteDictionary(dictionaryId: 100)
}
```
""")
    def delete_dictionary(self, info: strawberry.Info, dictionary_id: int) -> bool:
        from languages.services.dictionary_service import DictionaryService
        db = info.context["db"]
        service = DictionaryService(db)
        return service.delete(dictionary_id)
