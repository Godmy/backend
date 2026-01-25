# Advanced Search & Filtering

Powerful full-text search functionality for concepts and translations with filtering, sorting, and pagination.

## Features

- PostgreSQL full-text search (case-insensitive)
- Multi-language search across translations
- Filtering by language, category path, date range
- Multiple sort options (relevance, alphabetical, date)
- Pagination with total count and "has_more" indicator
- Autocomplete/suggestions for search input
- Popular concepts query
- N+1 query prevention with eager loading

## GraphQL API

See [docs/graphql/query/search.md](../graphql/query/search.md) for complete API documentation with examples.

## Sort Options

### Relevance (Default)
- **Algorithm:** Best match first by depth and query match
- **Use case:** Default search results
- **Performance:** Good (indexed)

**Relevance factors:**
1. Exact matches ranked higher
2. Shallow concepts (lower depth) ranked higher
3. Multiple word matches ranked higher

### Alphabetical
- **Algorithm:** Sort by concept path A-Z
- **Use case:** Browse concepts in order
- **Performance:** Excellent (indexed)

### Date
- **Algorithm:** Newest concepts first
- **Use case:** Recently added content
- **Performance:** Excellent (indexed on created_at)

## Search Types

### Full-Text Search

Search across concept paths and translations:

**Example queries:**
- `"user"` - Finds "user", "users", "user_profile"
- `"пользователь"` - Finds Russian translations
- `"auth login"` - Finds concepts with both terms

**Features:**
- Case-insensitive
- Partial word matching
- Multi-language support
- Accent-insensitive

### Autocomplete/Suggestions

Fast suggestions for search input:

**Characteristics:**
- Returns top 5-20 matches
- Optimized for speed (<50ms)
- Prefix-based matching
- Language-aware

### Category Filtering

Filter by concept path prefix:

**Examples:**
- `/users/` - All concepts under users
- `/auth/` - All authentication concepts
- `/api/` - All API-related concepts

## Implementation

### Service Layer

- `languages/services/search_service.py` - SearchService with all search logic
- `languages/schemas/search.py` - GraphQL schema with 3 queries

### Database Queries

**Search query structure:**
```python
from sqlalchemy import or_, and_
from sqlalchemy.orm import joinedload

query = (
    db.query(ConceptModel)
    .join(DictionaryModel)
    .filter(
        and_(
            ConceptModel.deleted_at.is_(None),
            DictionaryModel.deleted_at.is_(None),
            or_(
                ConceptModel.path.ilike(f"%{search_query}%"),
                DictionaryModel.name.ilike(f"%{search_query}%"),
                DictionaryModel.description.ilike(f"%{search_query}%")
            )
        )
    )
    .options(joinedload(ConceptModel.dictionaries))
)
```

### Optimization Techniques

1. **PostgreSQL ILIKE** - Case-insensitive search with index support
2. **joinedload** - Eager loading to prevent N+1 queries
3. **Soft-delete aware** - Only searches active records
4. **Indexed columns** - Fast lookups on path, language_id, concept_id

## Performance Tips

### Query Optimization

```python
# BAD - Multiple queries (N+1 problem)
concepts = db.query(Concept).filter(...).all()
for concept in concepts:
    translations = concept.dictionaries  # Triggers separate query!

# GOOD - Single query with eager loading
concepts = (
    db.query(Concept)
    .options(joinedload(Concept.dictionaries))
    .filter(...)
    .all()
)
```

### Pagination

```python
# Always use limit/offset
results = query.limit(20).offset(0).all()

# For large offsets, use cursor-based pagination
last_id = results[-1].id if results else 0
next_page = query.filter(Concept.id > last_id).limit(20).all()
```

### Language Filtering

```python
# BAD - Load all translations then filter
concepts = db.query(Concept).all()
filtered = [c for c in concepts if any(d.language_id in [1,2] for d in c.dictionaries)]

# GOOD - Filter in database
concepts = (
    db.query(Concept)
    .join(Dictionary)
    .filter(Dictionary.language_id.in_([1, 2]))
    .all()
)
```

## Search Configuration

### Limits

- **Search results:** Max 100 per page (default: 20)
- **Suggestions:** Max 20 results (default: 5)
- **Popular concepts:** Max 50 results (default: 10)

### Indexes

Required database indexes for optimal performance:

```sql
-- Concept path index (for category filtering)
CREATE INDEX idx_concept_path ON concepts(path);

-- Dictionary concept_id index (for joins)
CREATE INDEX idx_dictionary_concept_id ON dictionaries(concept_id);

-- Dictionary language_id index (for language filtering)
CREATE INDEX idx_dictionary_language_id ON dictionaries(language_id);

-- Concept created_at index (for date sorting)
CREATE INDEX idx_concept_created_at ON concepts(created_at);

-- Soft delete indexes
CREATE INDEX idx_concept_deleted_at ON concepts(deleted_at);
CREATE INDEX idx_dictionary_deleted_at ON dictionaries(deleted_at);
```

## Usage Examples

### Basic Search

```python
from languages.services.search_service import SearchService

search_service = SearchService(db)

results = search_service.search_concepts(
    query="user",
    limit=20,
    offset=0
)

for result in results["results"]:
    concept = result["concept"]
    translations = result["dictionaries"]
    print(f"{concept.path}: {translations[0].name}")
```

### Search with Filters

```python
results = search_service.search_concepts(
    query="auth",
    language_ids=[1, 2],  # English and Russian
    category_path="/api/",
    from_date=datetime(2024, 1, 1),
    to_date=datetime(2025, 12, 31),
    sort_by="RELEVANCE",
    limit=20
)
```

### Autocomplete

```python
suggestions = search_service.get_suggestions(
    query="us",
    language_id=1,
    limit=5
)

# Returns: ["user", "users", "user_profile", ...]
```

### Popular Concepts

```python
popular = search_service.get_popular_concepts(
    limit=10,
    language_id=1
)

# Returns most frequently accessed concepts
```

## Frontend Integration

### React Example

```typescript
import { useQuery } from '@apollo/client';
import { SEARCH_CONCEPTS } from './queries';

function SearchComponent() {
  const [query, setQuery] = useState('');
  const { data, loading } = useQuery(SEARCH_CONCEPTS, {
    variables: {
      filters: {
        query,
        limit: 20,
        offset: 0,
        sortBy: 'RELEVANCE'
      }
    },
    skip: query.length < 2
  });

  return (
    <div>
      <input
        value={query}
        onChange={e => setQuery(e.target.value)}
        placeholder="Search concepts..."
      />
      {loading && <Spinner />}
      {data && (
        <SearchResults results={data.searchConcepts.results} />
      )}
    </div>
  );
}
```

### Debounced Search

```typescript
import { useMemo } from 'react';
import debounce from 'lodash/debounce';

function SearchComponent() {
  const [query, setQuery] = useState('');

  const debouncedSearch = useMemo(
    () => debounce((value: string) => {
      // Trigger search
      refetch({ filters: { query: value } });
    }, 300),
    []
  );

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value);
    debouncedSearch(e.target.value);
  };

  return <input value={query} onChange={handleChange} />;
}
```

### Infinite Scroll

```typescript
import { useInfiniteQuery } from '@tanstack/react-query';

function SearchResults() {
  const {
    data,
    fetchNextPage,
    hasNextPage
  } = useInfiniteQuery({
    queryKey: ['search', query],
    queryFn: ({ pageParam = 0 }) =>
      searchConcepts({
        query,
        limit: 20,
        offset: pageParam
      }),
    getNextPageParam: (lastPage, pages) =>
      lastPage.hasMore ? pages.length * 20 : undefined
  });

  return (
    <InfiniteScroll
      dataLength={data?.pages.length ?? 0}
      next={fetchNextPage}
      hasMore={hasNextPage}
    >
      {data?.pages.map(page =>
        page.results.map(result => (
          <SearchResult key={result.concept.id} {...result} />
        ))
      )}
    </InfiniteScroll>
  );
}
```

## Advanced Features

### Search Highlighting

```python
def highlight_matches(text: str, query: str) -> str:
    """Highlight search terms in text"""
    import re
    pattern = re.compile(f"({re.escape(query)})", re.IGNORECASE)
    return pattern.sub(r"<mark>\1</mark>", text)

# Usage
for result in results["results"]:
    name = result["dictionaries"][0].name
    highlighted = highlight_matches(name, query)
    print(highlighted)
```

### Search Analytics

```python
from core.metrics import search_queries_total

def track_search(query: str, results_count: int):
    """Track search queries for analytics"""
    search_queries_total.labels(
        query_length=len(query),
        has_results=results_count > 0
    ).inc()
```

### Search Filters UI

```typescript
interface SearchFilters {
  query: string;
  languageIds: number[];
  categoryPath?: string;
  fromDate?: Date;
  toDate?: Date;
  sortBy: 'RELEVANCE' | 'ALPHABET' | 'DATE';
}

function SearchFiltersPanel({ filters, onChange }: Props) {
  return (
    <div>
      <LanguageSelect
        value={filters.languageIds}
        onChange={ids => onChange({ ...filters, languageIds: ids })}
      />
      <CategorySelect
        value={filters.categoryPath}
        onChange={path => onChange({ ...filters, categoryPath: path })}
      />
      <DateRangePicker
        from={filters.fromDate}
        to={filters.toDate}
        onChange={(from, to) => onChange({ ...filters, fromDate: from, toDate: to })}
      />
      <SortSelect
        value={filters.sortBy}
        onChange={sort => onChange({ ...filters, sortBy: sort })}
      />
    </div>
  );
}
```

## Troubleshooting

### Slow Search Performance

**Symptoms:**
- Search takes >1 second
- Database CPU usage high
- Many database queries

**Solutions:**
1. Add missing indexes
2. Use EXPLAIN ANALYZE to identify slow queries
3. Reduce result limit
4. Add caching layer (Redis)

### No Results Found

**Symptoms:**
- Valid search returns empty results
- Known concepts not appearing

**Checks:**
1. Verify concepts are not soft-deleted
2. Check language filter matches translation language
3. Verify category path format (should start with `/`)
4. Check date range includes concept creation date

### Incorrect Relevance Ranking

**Symptoms:**
- Less relevant results appear first
- Exact matches not prioritized

**Solutions:**
1. Adjust relevance scoring algorithm
2. Add weights to different fields
3. Use PostgreSQL full-text search (pg_trgm)
4. Implement custom scoring function

## Related Documentation

- GraphQL API: [Query Documentation](../graphql/query/search.md)
- [Database Optimization](../PERFORMANCE.md)
- [Caching Strategy](../CACHING.md)
