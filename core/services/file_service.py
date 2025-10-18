"""
Бизнес-логика для работы с файлами
"""
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from core.models.file import File
from core.file_storage import file_storage_service, ALLOWED_IMAGE_TYPES, MAX_AVATAR_SIZE


class FileService:
    """Сервис для работы с файлами"""

    def __init__(self, db: Session):
        self.db = db
        self.storage = file_storage_service

    def upload_file(
        self,
        file_content: bytes,
        filename: str,
        mime_type: str,
        file_type: str,
        user_id: int,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Загрузка файла

        Args:
            file_content: содержимое файла
            filename: оригинальное имя файла
            mime_type: MIME тип
            file_type: тип файла (avatar, attachment, image)
            user_id: ID пользователя
            entity_type: тип связанной сущности
            entity_id: ID связанной сущности

        Returns:
            Dict с информацией о файле
        """
        # Валидация размера
        max_size = (
            MAX_AVATAR_SIZE if file_type == "avatar" else self.storage.__class__.MAX_FILE_SIZE
        )
        valid, error = self.storage.validate_file_size(len(file_content), max_size)
        if not valid:
            raise ValueError(error)

        # Валидация MIME типа для изображений
        if file_type in ("avatar", "image"):
            valid, error = self.storage.validate_mime_type(mime_type, ALLOWED_IMAGE_TYPES)
            if not valid:
                raise ValueError(error)

        # Очистка имени файла
        safe_filename = self.storage.sanitize_filename(filename)

        # Сохранение файла
        stored_filename, filepath = self.storage.save_file(file_content, safe_filename)

        # Получение размеров изображения
        width, height = None, None
        if mime_type in ALLOWED_IMAGE_TYPES:
            width, height = self.storage.get_image_dimensions(file_content)

        # Создание thumbnail для изображений
        has_thumbnail = False
        thumbnail_path = None
        if file_type in ("avatar", "image") and mime_type in ALLOWED_IMAGE_TYPES:
            success, thumb_path = self.storage.create_thumbnail(file_content, stored_filename)
            if success:
                has_thumbnail = True
                thumbnail_path = thumb_path

        # Создание записи в БД
        file_model = File(
            filename=safe_filename,
            stored_filename=stored_filename,
            filepath=filepath,
            mime_type=mime_type,
            size=len(file_content),
            file_type=file_type,
            width=width,
            height=height,
            has_thumbnail=has_thumbnail,
            thumbnail_path=thumbnail_path,
            uploaded_by=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
        )

        self.db.add(file_model)
        self.db.commit()
        self.db.refresh(file_model)

        return {
            "id": file_model.id,
            "filename": file_model.filename,
            "url": file_model.url,
            "thumbnail_url": file_model.thumbnail_url,
            "size": file_model.size,
            "size_mb": file_model.size_mb,
            "mime_type": file_model.mime_type,
            "width": file_model.width,
            "height": file_model.height,
        }

    def get_file_by_id(self, file_id: int) -> Optional[File]:
        """Получение файла по ID"""
        return self.db.query(File).filter(File.id == file_id).first()

    def get_file_by_stored_filename(self, stored_filename: str) -> Optional[File]:
        """Получение файла по имени в хранилище"""
        return (
            self.db.query(File).filter(File.stored_filename == stored_filename).first()
        )

    def get_user_files(
        self, user_id: int, file_type: Optional[str] = None, limit: int = 50
    ) -> list[File]:
        """Получение файлов пользователя"""
        query = self.db.query(File).filter(File.uploaded_by == user_id)

        if file_type:
            query = query.filter(File.file_type == file_type)

        return query.order_by(File.created_at.desc()).limit(limit).all()

    def delete_file(self, file_id: int, user_id: int) -> bool:
        """Удаление файла"""
        file_model = self.get_file_by_id(file_id)

        if not file_model:
            raise ValueError("File not found")

        if file_model.uploaded_by != user_id:
            raise PermissionError("You don't have permission to delete this file")

        # Удаление файла с диска
        self.storage.delete_file(file_model.filepath)

        # Удаление thumbnail
        if file_model.has_thumbnail:
            self.storage.delete_thumbnail(file_model.stored_filename)

        # Удаление из БД
        self.db.delete(file_model)
        self.db.commit()

        return True

    def update_avatar(self, user_id: int, file_id: int) -> bool:
        """Обновление аватара пользователя"""
        from auth.models.profile import UserProfileModel

        # Проверка что файл существует и принадлежит пользователю
        file_model = self.get_file_by_id(file_id)
        if not file_model:
            raise ValueError("File not found")

        if file_model.uploaded_by != user_id:
            raise PermissionError("File doesn't belong to you")

        if file_model.file_type != "avatar":
            raise ValueError("File is not an avatar")

        # Обновление профиля
        profile = (
            self.db.query(UserProfileModel)
            .filter(UserProfileModel.user_id == user_id)
            .first()
        )

        if not profile:
            raise ValueError("Profile not found")

        # Удаление старого аватара если есть
        if profile.avatar_file_id:
            old_file = self.get_file_by_id(profile.avatar_file_id)
            if old_file:
                try:
                    self.delete_file(old_file.id, user_id)
                except Exception:
                    pass  # Игнорируем ошибки удаления старого файла

        profile.avatar_file_id = file_id
        profile.avatar = file_model.url

        self.db.commit()

        return True
