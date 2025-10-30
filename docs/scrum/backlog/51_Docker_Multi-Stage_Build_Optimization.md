### #51 - Docker Multi-Stage Build Optimization

**User Story:**
Как DevOps инженер, я хочу оптимизировать Docker build, чтобы ускорить deployment и снизить image size.

**Acceptance Criteria:**
- [ ] Multi-stage Dockerfile
- [ ] Build dependencies в separate stage
- [ ] Image size <200MB (сейчас ~500MB)
- [ ] Layer caching optimization
- [ ] .dockerignore для исключения лишних файлов
- [ ] Security scanning (Trivy/Grype)

**Estimated Effort:** 5 story points

**Status:** 📋 Backlog