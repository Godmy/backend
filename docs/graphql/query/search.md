# Advanced Search & Filtering Queries

## Full-Text Search

Search concepts and translations with filters, sorting, and pagination.

```graphql
query SearchConcepts {
  searchConcepts(
    filters: {
      query: "пользователь"
      languageIds: [1, 2]  # Russian and English
      categoryPath: "/users/"
      fromDate: "2024-01-01T00:00:00"
      toDate: "2025-01-31T23:59:59"
      sortBy: RELEVANCE
      limit: 20
      offset: 0
    }
  ) {
    results {
      concept {
        id
        path
        depth
      }
      dictionaries {
        id
        name
        description
        languageId
      }
      relevanceScore
    }
    total
    hasMore
    limit
    offset
  }
}
```

**Filter options:**
- `query` - Search text (case-insensitive)
- `languageIds` - Filter by language IDs
- `categoryPath` - Filter by concept path prefix
- `fromDate`, `toDate` - Date range filter
- `sortBy` - Sort order (RELEVANCE, ALPHABET, DATE)
- `limit` - Max results per page (max 100)
- `offset` - Pagination offset

**Sort options:**
- `RELEVANCE` - Best match first (by depth and query match)
- `ALPHABET` - Alphabetical by concept path
- `DATE` - Newest concepts first

---

## Search Suggestions (Autocomplete)

Get search suggestions for autocomplete.

```graphql
query SearchSuggestions {
  searchSuggestions(query: "user", languageId: 1, limit: 5)
}
```

**Returns:** Array of suggested search terms

**Use case:** Provide autocomplete suggestions as user types

---

## Popular Concepts

Get most commonly used concepts.

```graphql
query PopularConcepts {
  popularConcepts(limit: 10) {
    concept {
      id
      path
    }
    dictionaries {
      name
      description
    }
    relevanceScore
  }
}
```

---

## Search Features

- **PostgreSQL full-text search** (case-insensitive)
- **Multi-language search** across all translations
- **N+1 query prevention** with eager loading (`joinedload`)
- **Soft-delete aware** (only searches active records)
- **Indexed columns** for performance

**Performance:**
- Results limited to max 100 per page
- Suggestions limited to max 20
- Indexed: `concept.path`, `dictionary.language_id`, `dictionary.concept_id`

---

## Frontend Example

```typescript
// Search with debouncing
const searchConcepts = async (query: string, languageIds: number[]) => {
  const result = await graphqlClient.query({
    query: SEARCH_CONCEPTS_QUERY,
    variables: {
      filters: {
        query,
        languageIds,
        limit: 20,
        offset: 0,
        sortBy: 'RELEVANCE'
      }
    }
  });
  return result.data.searchConcepts;
};

// Autocomplete with debouncing
const getSuggestions = async (query: string) => {
  if (query.length < 2) return [];

  const result = await graphqlClient.query({
    query: SEARCH_SUGGESTIONS_QUERY,
    variables: { query, limit: 5 }
  });
  return result.data.searchSuggestions;
};
```

---

## Implementation

- `languages/services/search_service.py` - SearchService
- `languages/schemas/search.py` - GraphQL schema
- Uses PostgreSQL `ILIKE` for case-insensitive search
