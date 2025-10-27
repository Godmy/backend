"""
GraphQL schemas for managing concepts, which form the hierarchical structure of the ontology.
"""

from typing import List, Optional
import strawberry

# ============================================================================
# Types
# ============================================================================

@strawberry.type(description="Represents a language associated with a dictionary entry.")
class ConceptLanguage:
    code: str = strawberry.field(description="The language code (e.g., 'en', 'ru').")

@strawberry.type(description="Represents a translation (dictionary entry) for a concept.")
class ConceptDictionary:
    name: str = strawberry.field(description="The name of the concept in this language.")
    description: Optional[str] = strawberry.field(description="A detailed description in this language.")
    language: ConceptLanguage = strawberry.field(description="The language of this translation.")

@strawberry.type(description="""Represents a concept in the ontology's hierarchy.

Concepts use a materialized path pattern (e.g., 'science.physics.relativity') to represent their position.
""")
class Concept:
    id: int = strawberry.field(description="Unique identifier for the concept.")
    parent_id: Optional[int] = strawberry.field(description="The ID of the parent concept. Null for root concepts.")
    path: str = strawberry.field(description="The materialized path (e.g., 'colors.red').")
    depth: int = strawberry.field(description="The depth in the hierarchy (0 for root concepts).")
    dictionaries: List[ConceptDictionary] = strawberry.field(
        description="List of translations for this concept.",
        default_factory=list
    )

# ============================================================================
# Inputs
# ============================================================================

@strawberry.input(description="Input for creating a new concept.")
class ConceptInput:
    path: str = strawberry.field(description="Materialized path. Must include parent's path (e.g., 'parent.child').")
    depth: int = strawberry.field(description="Depth of the concept (should be parent.depth + 1).")
    parent_id: Optional[int] = strawberry.field(default=None, description="The ID of the parent concept. Null to create a root concept.")

@strawberry.input(description="Input for updating an existing concept.")
class ConceptUpdateInput:
    path: Optional[str] = strawberry.field(default=None, description="The new materialized path.")
    depth: Optional[int] = strawberry.field(default=None, description="The new depth.")
    parent_id: Optional[int] = strawberry.field(default=None, description="The new parent ID.")

# ============================================================================
# Queries
# ============================================================================

@strawberry.type
class ConceptQuery:
    """GraphQL queries for retrieving concepts."""

    @strawberry.field(description="""Get a list of concepts. Can be filtered by parent or depth.

- Providing `parentId` fetches direct children of a concept.
- Providing `depth: 0` fetches only root concepts.
- Providing no arguments fetches all concepts.

Example (get children of concept 1):
```graphql
query GetChildConcepts {
  concepts(parentId: 1) {
    id
    path
    depth
  }
}
```
""")
    def concepts(
        self, info: strawberry.Info, depth: Optional[int] = None, parent_id: Optional[int] = None
    ) -> List[Concept]:
        from languages.services.concept_service import ConceptService
        db = info.context["db"]
        service = ConceptService(db)

        if depth is not None and depth == 0:
            concepts_db = service.get_root_concepts()
        elif parent_id is not None:
            concepts_db = service.get_children(parent_id)
        else:
            concepts_db = service.get_all()

        return [self._map_concept_to_gql(c) for c in concepts_db]

    @strawberry.field(description="""Get a single concept by its unique ID, including its translations.

Example:
```graphql
query GetConceptDetails {
  concept(conceptId: 1) {
    id
    path
    dictionaries {
      name
      description
      language {
        code
      }
    }
  }
}
```
""")
    def concept(self, concept_id: int, info: strawberry.Info) -> Optional[Concept]:
        from languages.services.concept_service import ConceptService
        db = info.context["db"]
        service = ConceptService(db)
        concept_db = service.get_by_id(concept_id)
        return self._map_concept_to_gql(concept_db) if concept_db else None

    def _map_concept_to_gql(self, concept_db) -> Concept:
        return Concept(
            id=concept_db.id,
            parent_id=concept_db.parent_id,
            path=concept_db.path,
            depth=concept_db.depth,
            dictionaries=[
                ConceptDictionary(
                    name=d.name,
                    description=d.description,
                    language=ConceptLanguage(code=d.language.code)
                )
                for d in concept_db.dictionaries
            ]
        )

# ============================================================================
# Mutations
# ============================================================================

@strawberry.type
class ConceptMutation:
    """GraphQL mutations for creating, updating, and deleting concepts."""

    @strawberry.mutation(description="""Create a new concept.

To create a root concept, set `parentId` to `null` and `depth` to `0`.
To create a child, provide the `parentId` and set `depth` to `parent.depth + 1`.

Example (create a root concept):
```graphql
mutation CreateRootConcept {
  createConcept(input: {
    path: "sports"
    depth: 0
    parentId: null
  }) {
    id
    path
    depth
  }
}
```
""")
    def create_concept(self, info: strawberry.Info, input: ConceptInput) -> Concept:
        from languages.services.concept_service import ConceptService
        db = info.context["db"]
        service = ConceptService(db)
        concept_db = service.create(path=input.path, depth=input.depth, parent_id=input.parent_id)
        return ConceptQuery._map_concept_to_gql(self, concept_db)

    @strawberry.mutation(description="""Update an existing concept's path, depth, or parent.

Example:
```graphql
mutation UpdateConceptPath {
  updateConcept(conceptId: 5, input: { path: "games.boardgames" }) {
    id
    path
  }
}
```
""")
    def update_concept(self, info: strawberry.Info, concept_id: int, input: ConceptUpdateInput) -> Concept:
        from languages.services.concept_service import ConceptService
        db = info.context["db"]
        service = ConceptService(db)
        concept_db = service.update(
            concept_id, path=input.path, depth=input.depth, parent_id=input.parent_id
        )
        if not concept_db:
            raise Exception("Concept not found")
        return ConceptQuery._map_concept_to_gql(self, concept_db)

    @strawberry.mutation(description="""Soft delete a concept. This is a reversible action.

All child concepts and associated translations will also be soft-deleted.

Example:
```graphql
mutation DeleteConcept {
  deleteConcept(conceptId: 10)
}
```
""")
    def delete_concept(self, info: strawberry.Info, concept_id: int) -> bool:
        from languages.services.concept_service import ConceptService
        db = info.context["db"]
        service = ConceptService(db)
        return service.delete(concept_id)
