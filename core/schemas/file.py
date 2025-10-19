"""
GraphQL схемы для работы с файлами
"""

from typing import Optional

import strawberry
from sqlalchemy.orm import Session
from strawberry.file_uploads import Upload
from strawberry.types import Info

from core.models.file import File as FileModel
from core.services.file_service import FileService


@strawberry.type
class FileType:
    """GraphQL тип для файла"""

    id: int
    filename: str
    url: str
    thumbnail_url: Optional[str]
    mime_type: str
    size: int
    size_mb: float
    file_type: str
    width: Optional[int]
    height: Optional[int]
    created_at: str

    @staticmethod
    def from_model(file_model: FileModel) -> "FileType":
        """Создание из модели"""
        return FileType(
            id=file_model.id,
            filename=file_model.filename,
            url=file_model.url,
            thumbnail_url=file_model.thumbnail_url,
            mime_type=file_model.mime_type,
            size=file_model.size,
            size_mb=file_model.size_mb,
            file_type=file_model.file_type,
            width=file_model.width,
            height=file_model.height,
            created_at=file_model.created_at.isoformat(),
        )


@strawberry.input
class UploadFileInput:
    """Input для загрузки файла"""

    file: Upload
    file_type: str  # 'avatar', 'attachment', 'image'
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None


@strawberry.type
class FileQuery:
    """GraphQL queries для файлов"""

    @strawberry.field
    def my_files(
        self,
        info: Info,
        file_type: Optional[str] = None,
        limit: int = 50,
    ) -> list[FileType]:
        """Получить мои файлы"""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")

        db: Session = info.context["db"]
        service = FileService(db)

        files = service.get_user_files(user.id, file_type, limit)
        return [FileType.from_model(f) for f in files]

    @strawberry.field
    def file(self, info: Info, file_id: int) -> Optional[FileType]:
        """Получить файл по ID"""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")

        db: Session = info.context["db"]
        service = FileService(db)

        file_model = service.get_file_by_id(file_id)
        if not file_model:
            return None

        # Проверка прав доступа
        if file_model.uploaded_by != user.id:
            raise Exception("Access denied")

        return FileType.from_model(file_model)


@strawberry.type
class FileMutation:
    """GraphQL mutations для файлов"""

    @strawberry.mutation
    async def upload_avatar(self, info: Info, file: Upload) -> FileType:
        """Загрузка аватара"""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")

        db: Session = info.context["db"]
        service = FileService(db)

        # Чтение файла
        file_content = await file.read()

        try:
            # Загрузка
            result = service.upload_file(
                file_content=file_content,
                filename=file.filename,
                mime_type=file.content_type or "application/octet-stream",
                file_type="avatar",
                user_id=user.id,
                entity_type="profile",
                entity_id=user.id,
            )

            # Обновление аватара в профиле
            service.update_avatar(user.id, result["id"])

            # Получение файла
            file_model = service.get_file_by_id(result["id"])
            return FileType.from_model(file_model)

        except ValueError as e:
            raise Exception(str(e))
        except PermissionError as e:
            raise Exception(str(e))

    @strawberry.mutation
    async def upload_file(self, info: Info, input: UploadFileInput) -> FileType:
        """Загрузка файла"""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")

        db: Session = info.context["db"]
        service = FileService(db)

        # Чтение файла
        file_content = await input.file.read()

        try:
            # Загрузка
            result = service.upload_file(
                file_content=file_content,
                filename=input.file.filename,
                mime_type=input.file.content_type or "application/octet-stream",
                file_type=input.file_type,
                user_id=user.id,
                entity_type=input.entity_type,
                entity_id=input.entity_id,
            )

            # Получение файла
            file_model = service.get_file_by_id(result["id"])
            return FileType.from_model(file_model)

        except ValueError as e:
            raise Exception(str(e))
        except PermissionError as e:
            raise Exception(str(e))

    @strawberry.mutation
    def delete_file(self, info: Info, file_id: int) -> bool:
        """Удаление файла"""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")

        db: Session = info.context["db"]
        service = FileService(db)

        try:
            return service.delete_file(file_id, user.id)
        except ValueError as e:
            raise Exception(str(e))
        except PermissionError as e:
            raise Exception(str(e))
