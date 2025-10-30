### #18 - Background Task Processing (Celery) ✅

**User Story:**
Как разработчик, я хочу выполнять длительные задачи асинхронно (отправка email, генерация отчетов), чтобы не блокировать HTTP requests.

**Acceptance Criteria:**
- [✅] Celery integration с Redis/RabbitMQ broker
- [✅] Задачи: отправка email, генерация thumbnails, очистка старых файлов
- [✅] Celery beat для периодических задач
- [✅] Monitoring задач (Flower или Prometheus)
- [✅] Retry logic с exponential backoff
- [ ] Dead letter queue для failed tasks
- [✅] Graceful shutdown

**Estimated Effort:** 13 story points

**Status:** ✅ Done

**Implementation Details:**
- Интеграция Celery, Flower, и Redis добавлена в `docker-compose.dev.yml`.
- Асинхронные задачи определены в директории `tasks/` для email, файлов и периодических проверок.
- Воркеры запускаются через `workers/celery_worker.py`.
- Реализована логика повторных попыток с экспоненциальной задержкой.
- Мониторинг доступен через веб-интерфейс Flower.