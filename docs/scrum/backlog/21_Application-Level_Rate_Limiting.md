### #21 - Application-Level Rate Limiting 🎯

**User Story:**
Как разработчик, я хочу rate limiting на уровне приложения (не только nginx), чтобы защититься от abuse в GraphQL queries.

**Acceptance Criteria:**
- [✅] Middleware для подсчета запросов per user/IP
- [✅] Redis для distributed rate limiting
- [✅] Разные лимиты для разных endpoints
- [⏸️] GraphQL query complexity analysis (future enhancement)
- [⏸️] Throttling для expensive queries (future enhancement)
- [✅] HTTP 429 с Retry-After header

**Estimated Effort:** 8 story points

**Status:** 🎯 67% Complete (2025-10-26) - Core functionality done

**Implementation Details:**
- Implemented as part of #5 (API Rate Limiting)
- `core/middleware/rate_limit.py` - Extended with per-endpoint limits
- Per-endpoint rate limits via JSON config: RATE_LIMIT_ENDPOINT_LIMITS
- Regex patterns for flexible endpoint matching
- Example: `{"^/graphql$": {"auth": 50, "anon": 10}, "^/api/search": {"auth": 30, "anon": 5}}`
- Fallback to global limits when endpoint not matched
- Per-endpoint counters in Redis
- All features from #5 apply per-endpoint

**Completed (4/6 criteria):**
- ✅ Middleware for request counting
- ✅ Redis distributed rate limiting
- ✅ Different limits per endpoint
- ✅ HTTP 429 with Retry-After

**Future Enhancements (2/6 criteria):**
- ⏸️ GraphQL query complexity analysis (requires AST parsing)
- ⏸️ Smart throttling based on query complexity

**Files Modified:**
- core/middleware/rate_limit.py (UPDATED - added per-endpoint limits)
- .env.example (UPDATED - RATE_LIMIT_ENDPOINT_LIMITS)
- tests/test_rate_limiting.py (UPDATED - 3 new tests for per-endpoint)
- docs/features/rate_limiting.md (UPDATED - per-endpoint documentation)