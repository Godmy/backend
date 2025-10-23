# Concept Mutations

**Required:** Authorization header

## Create Root Concept

Create a new root concept (top-level).

```graphql
mutation CreateConcept {
  createConcept(input: {
    path: "sports"
    depth: 0
    parentId: null
  }) {
    id
    path
    depth
    createdAt
  }
}
```

---

## Create Child Concept

Create a child concept under existing parent.

```graphql
mutation CreateChildConcept {
  createConcept(input: {
    path: "sports.football"
    depth: 1
    parentId: 50
  }) {
    id
    path
    depth
    parentId
  }
}
```

**Notes:**
- Parent concept must exist
- Depth should be parent.depth + 1
- Path should include parent path

---

## Update Concept

Update existing concept.

```graphql
mutation UpdateConcept {
  updateConcept(
    id: 1
    input: {
      path: "technology"
    }
  ) {
    id
    path
    updatedAt
  }
}
```

---

## Delete Concept

Soft delete a concept.

```graphql
mutation DeleteConcept {
  deleteConcept(id: 100)  # Returns boolean
}
```

**Notes:**
- Uses soft delete (can be restored by admin)
- Deletes all child concepts recursively
- Deletes all translations

---

## Example Workflow

Create concept hierarchy with translations:

```graphql
# Step 1: Create root concept
mutation CreateRoot {
  createConcept(input: {
    path: "technology"
    depth: 0
    parentId: null
  }) {
    id
  }
}

# Step 2: Add translations (see dictionary mutations)

# Step 3: Create child concept
mutation CreateChild {
  createConcept(input: {
    path: "technology.programming"
    depth: 1
    parentId: 100  # ID from step 1
  }) {
    id
  }
}
```

---

## Implementation

- `languages/models/concept.py` - ConceptModel
- `languages/schemas/concept.py` - GraphQL schema
- `languages/services/concept_service.py` - Business logic
