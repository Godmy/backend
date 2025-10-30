### #19 - Structured Logging (JSON Format) ✅

**User Story:**
Как DevOps инженер, я хочу логи в JSON формате, чтобы легко их парсить и анализировать в ELK/CloudWatch.

**Acceptance Criteria:**
- [✅] JSON logging format (python-json-logger)
- [✅] Поля: timestamp, level, message, request_id, user_id, endpoint
- [✅] Correlation ID для трассировки request-ов
- [✅] Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- [✅] Rotation политика (по размеру/времени)
- [✅] Separate logs: access.log, error.log, app.log
- [✅] ELK/CloudWatch compatibility

**Estimated Effort:** 8 story points

**Status:** ✅ Done (2025-01-26)

**Implementation Details:**
- `core/structured_logging.py` - CustomJsonFormatter with context support
- Automatic fields: timestamp, level, logger, module, function, line, request_id, user_id
- Integrated with existing middleware (RequestLoggingMiddleware)
- Added to critical places: auth, database, GraphQL operations
- File rotation: 10MB per file, 5 backup files
- Environment variables: LOG_LEVEL, LOG_FORMAT, LOG_DIR, LOG_FILE_ENABLED
- Fallback to text format when python-json-logger not available
- Convenience functions: log_api_request(), log_database_query(), log_business_event()

**Files Modified:**
- core/structured_logging.py (NEW, 342 lines)
- auth/services/auth_service.py (UPDATED - added structured logging)
- auth/utils/jwt_handler.py (UPDATED - added token verification logging)
- core/database.py (UPDATED - structured logging for DB errors)
- core/graphql_extensions.py (UPDATED - GraphQL operation logging)
- docs/features/structured_logging.md (NEW, 400+ lines)
- docs/features/README.md (UPDATED)
- CLAUDE.md (UPDATED)