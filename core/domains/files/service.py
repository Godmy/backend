from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from core.models.file import File


class FileService:
    def __init__(self, db: Session):
        self.db = db
        self.upload_dir = Path(os.getenv("UPLOAD_DIR", "uploads"))
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def get_user_files(self, user_id: int, file_type: str | None = None, limit: int = 50):
        query = self.db.query(File).filter(File.uploaded_by == user_id)
        if file_type:
            query = query.filter(File.file_type == file_type)
        return query.order_by(File.created_at.desc()).limit(limit).all()

    def get_file_by_id(self, file_id: int) -> File | None:
        return self.db.query(File).filter(File.id == file_id).first()

    def upload_file(
        self,
        file_content: bytes,
        filename: str,
        mime_type: str,
        file_type: str,
        user_id: int,
        entity_type: str | None = None,
        entity_id: int | None = None,
    ) -> dict[str, Any]:
        stored_filename = f"{uuid.uuid4().hex}_{filename}"
        filepath = self.upload_dir / stored_filename
        filepath.write_bytes(file_content)

        file_model = File(
            filename=filename,
            stored_filename=stored_filename,
            filepath=str(filepath),
            mime_type=mime_type,
            size=len(file_content),
            file_type=file_type,
            uploaded_by=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        self.db.add(file_model)
        self.db.commit()
        self.db.refresh(file_model)
        return {"id": file_model.id, "url": file_model.url}

    def update_avatar(self, user_id: int, file_id: int) -> None:
        return None

    def delete_file(self, file_id: int, user_id: int) -> bool:
        file_model = self.get_file_by_id(file_id)
        if file_model is None:
            raise ValueError(f"File with ID {file_id} not found")
        if file_model.uploaded_by != user_id:
            raise PermissionError("You can only delete your own files")

        try:
            Path(file_model.filepath).unlink(missing_ok=True)
        except Exception:
            pass

        self.db.delete(file_model)
        self.db.commit()
        return True

