from __future__ import annotations

import io
import os
from pathlib import Path

from PIL import Image


class FileStorageService:
    def __init__(self) -> None:
        self.upload_dir = Path(os.getenv("UPLOAD_DIR", "uploads"))
        self.thumbnail_dir = self.upload_dir / "thumbnails"
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.thumbnail_dir.mkdir(parents=True, exist_ok=True)

    def create_thumbnail(
        self,
        file_content: bytes,
        stored_filename: str,
        max_size: tuple[int, int] = (320, 320),
    ) -> tuple[bool, str | None]:
        try:
            image = Image.open(io.BytesIO(file_content))
            image.thumbnail(max_size)

            output_path = self.thumbnail_dir / stored_filename
            image.save(output_path)
            return True, str(output_path)
        except Exception:
            return False, None


file_storage_service = FileStorageService()
