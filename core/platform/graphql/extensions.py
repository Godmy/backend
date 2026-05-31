from __future__ import annotations

from strawberry.extensions import SchemaExtension

from core.platform.db.database import SessionLocal


class DatabaseSessionExtension(SchemaExtension):
    def on_operation(self):
        db = SessionLocal()
        self.execution_context.context["db"] = db
        try:
            yield
        finally:
            db.close()

