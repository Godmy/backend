"""
GraphQL schemas for managing languages.
"""

from typing import List, Optional
import strawberry

# ============================================================================
# Types
# ============================================================================

@strawberry.type(description="Represents a language available for translations.")
class Language:
    id: int = strawberry.field(description="Unique identifier for the language.")
    code: str = strawberry.field(description="The language code (e.g., 'en', 'ru'). Must be unique.")
    name: str = strawberry.field(description="The full name of the language (e.g., 'English', 'Русский').")

# ============================================================================
# Inputs
# ============================================================================

@strawberry.input(description="Input for creating a new language.")
class LanguageInput:
    code: str = strawberry.field(description="The language code (e.g., 'fr').")
    name: str = strawberry.field(description="The full name of the language (e.g., 'Français').")

@strawberry.input(description="Input for updating an existing language.")
class LanguageUpdateInput:
    code: Optional[str] = strawberry.field(default=None, description="The new language code.")
    name: Optional[str] = strawberry.field(default=None, description="The new full name.")

# ============================================================================
# Queries
# ============================================================================

@strawberry.type
class LanguageQuery:
    """GraphQL queries for retrieving languages."""

    @strawberry.field(description="""Get a list of all available languages.

Example:
```graphql
query GetLanguages {
  languages {
    id
    code
    name
  }
}
```
""")
    def languages(self, info: strawberry.Info) -> List[Language]:
        from languages.services.language_service import LanguageService
        db = info.context["db"]
        service = LanguageService(db)
        languages_db = service.get_all()
        return [Language(id=lang.id, code=lang.code, name=lang.name) for lang in languages_db]

    @strawberry.field(description="Get a single language by its unique ID.")
    def language(self, language_id: int, info: strawberry.Info) -> Optional[Language]:
        from languages.services.language_service import LanguageService
        db = info.context["db"]
        service = LanguageService(db)
        lang_db = service.get_by_id(language_id)
        return Language(id=lang_db.id, code=lang_db.code, name=lang_db.name) if lang_db else None

# ============================================================================
# Mutations
# ============================================================================

@strawberry.type
class LanguageMutation:
    """GraphQL mutations for managing languages."""

    @strawberry.mutation(description="""Create a new language.

Example:
```graphql
mutation CreateItalianLanguage {
  createLanguage(input: { code: "it", name: "Italiano" }) {
    id
    code
    name
  }
}
```
""")
    def create_language(self, info: strawberry.Info, input: LanguageInput) -> Language:
        from languages.services.language_service import LanguageService
        db = info.context["db"]
        service = LanguageService(db)
        lang_db = service.create(code=input.code, name=input.name)
        return Language(id=lang_db.id, code=lang_db.code, name=lang_db.name)

    @strawberry.mutation(description="""Update an existing language.

Example:
```graphql
mutation UpdateRussianLanguage {
  updateLanguage(languageId: 1, input: { name: "Русский" }) {
    id
    name
  }
}
```
""")
    def update_language(self, info: strawberry.Info, language_id: int, input: LanguageUpdateInput) -> Language:
        from languages.services.language_service import LanguageService
        db = info.context["db"]
        service = LanguageService(db)
        lang_db = service.update(language_id, code=input.code, name=input.name)
        if not lang_db:
            raise Exception("Language not found")
        return Language(id=lang_db.id, code=lang_db.code, name=lang_db.name)

    @strawberry.mutation(description="""Soft delete a language. This is a reversible action.

A language cannot be deleted if it is currently associated with any translations.

Example:
```graphql
mutation DeleteLanguage {
  deleteLanguage(languageId: 10)
}
```
""")
    def delete_language(self, info: strawberry.Info, language_id: int) -> bool:
        from languages.services.language_service import LanguageService
        db = info.context["db"]
        service = LanguageService(db)
        return service.delete(language_id)
