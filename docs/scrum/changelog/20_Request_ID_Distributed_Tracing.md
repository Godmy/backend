### #20 - Request ID & Distributed Tracing ✅

**User Story:**
Как разработчик, я хочу уникальный request_id для каждого запроса, чтобы трассировать его через все сервисы и логи.

**Acceptance Criteria:**
- [✅] Middleware генерирует уникальный request_id (UUID)
- [✅] Request ID в response headers: `X-Request-ID`
- [✅] Request ID в логах всех компонентов
- [✅] Передача request_id в Celery tasks (via decorator)
- [✅] Context variables для thread-safe tracking
- [✅] GraphQL context integration
- [✅] Tracing helpers для manual instrumentation
- [⏸️] Интеграция с OpenTelemetry (future enhancement)

**Estimated Effort:** 8 story points

**Status:** ✅ Done (2025-10-20)

**Implementation Details:**
- `core/context.py` - Context variables (request_id, user_id) и RequestContextFilter
- `core/tracing.py` - Decorators (@with_request_context, @celery_task_with_context) и TracingHelper
- `core/middleware/request_logging.py` - Updated to set context variables
- `app.py` - Configured logging with request_id format
- `tests/test_request_tracing.py` - Complete test coverage
- Automatic logging format: `[request_id] [user:user_id] LEVEL - message`
- GraphQL context includes request_id for all resolvers
- Zero configuration - works out of the box

**Files Modified:**
- core/context.py (NEW)
- core/tracing.py (NEW)
- core/middleware/request_logging.py
- app.py
- tests/test_request_tracing.py (NEW)
- CLAUDE.md - Added comprehensive documentation