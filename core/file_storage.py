"""
Сервис для работы с файловым хранилищем
"""
import os
import uuid
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, BinaryIO
from PIL import Image
import io

# Конфигурация
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
THUMBNAIL_DIR = os.path.join(UPLOAD_DIR, "thumbnails")
MAX_AVATAR_SIZE = 5 * 1024 * 1024  # 5MB
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
THUMBNAIL_SIZE = (256, 256)


class FileStorageService:
    """Сервис для управления файловым хранилищем"""

    def __init__(self):
        """Инициализация сервиса"""
        self.upload_dir = Path(UPLOAD_DIR)
        self.thumbnail_dir = Path(THUMBNAIL_DIR)
        self._ensure_directories()

    def _ensure_directories(self):
        """Создание необходимых директорий"""
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.thumbnail_dir.mkdir(parents=True, exist_ok=True)

    def generate_filename(self, original_filename: str) -> str:
        """Генерация безопасного уникального имени файла"""
        # Получаем расширение
        ext = Path(original_filename).suffix.lower()
        # Генерируем уникальное имя
        unique_id = uuid.uuid4().hex
        timestamp = datetime.utcnow().strftime("%Y%m%d")
        return f"{timestamp}_{unique_id}{ext}"

    def sanitize_filename(self, filename: str) -> str:
        """Очистка имени файла от опасных символов"""
        # Удаляем путь, оставляем только имя файла
        filename = os.path.basename(filename)
        # Удаляем опасные символы
        safe_chars = "-_.() "
        filename = "".join(
            c for c in filename if c.isalnum() or c in safe_chars
        ).rstrip()
        return filename[:255]  # Ограничение длины

    def validate_file_size(
        self, file_size: int, max_size: int = MAX_FILE_SIZE
    ) -> Tuple[bool, Optional[str]]:
        """Валидация размера файла"""
        if file_size > max_size:
            max_mb = max_size / (1024 * 1024)
            return False, f"File size exceeds {max_mb}MB limit"
        if file_size == 0:
            return False, "File is empty"
        return True, None

    def validate_mime_type(
        self, mime_type: str, allowed_types: set = None
    ) -> Tuple[bool, Optional[str]]:
        """Валидация MIME типа файла"""
        if allowed_types is None:
            allowed_types = ALLOWED_IMAGE_TYPES

        if mime_type not in allowed_types:
            return False, f"File type {mime_type} not allowed"
        return True, None

    def save_file(
        self, file_content: bytes, filename: str
    ) -> Tuple[str, str]:
        """
        Сохранение файла на диск

        Returns:
            Tuple[stored_filename, filepath]
        """
        stored_filename = self.generate_filename(filename)
        filepath = self.upload_dir / stored_filename

        with open(filepath, "wb") as f:
            f.write(file_content)

        return stored_filename, str(filepath)

    def get_image_dimensions(
        self, file_content: bytes
    ) -> Tuple[Optional[int], Optional[int]]:
        """Получение размеров изображения"""
        try:
            image = Image.open(io.BytesIO(file_content))
            return image.width, image.height
        except Exception:
            return None, None

    def create_thumbnail(
        self, file_content: bytes, stored_filename: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Создание thumbnail для изображения

        Returns:
            Tuple[success, thumbnail_path]
        """
        try:
            image = Image.open(io.BytesIO(file_content))

            # Конвертируем в RGB если нужно
            if image.mode in ("RGBA", "P"):
                image = image.convert("RGB")

            # Создаем thumbnail
            image.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)

            # Сохраняем
            thumbnail_path = self.thumbnail_dir / stored_filename
            image.save(thumbnail_path, "JPEG", quality=85, optimize=True)

            return True, str(thumbnail_path)
        except Exception as e:
            print(f"Error creating thumbnail: {e}")
            return False, None

    def delete_file(self, filepath: str) -> bool:
        """Удаление файла"""
        try:
            path = Path(filepath)
            if path.exists():
                path.unlink()
                return True
        except Exception as e:
            print(f"Error deleting file: {e}")
        return False

    def delete_thumbnail(self, stored_filename: str) -> bool:
        """Удаление thumbnail"""
        thumbnail_path = self.thumbnail_dir / stored_filename
        return self.delete_file(str(thumbnail_path))

    def calculate_file_hash(self, file_content: bytes) -> str:
        """Вычисление SHA256 хэша файла"""
        return hashlib.sha256(file_content).hexdigest()


# Singleton instance
file_storage_service = FileStorageService()
