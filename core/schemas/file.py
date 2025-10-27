'''"""
GraphQL schemas for file uploads and management.
"""

from typing import List, Optional
import strawberry
from sqlalchemy.orm import Session
from strawberry.file_uploads import Upload
from strawberry.types import Info

from core.models.file import File as FileModel
from core.services.file_service import FileService

# ============================================================================
# Types
# ============================================================================

@strawberry.type(description="Represents an uploaded file.")
class FileType:
    id: int
    filename: str = strawberry.field(description="Sanitized filename on disk.")
    url: str = strawberry.field(description="Public URL to access the file.")
    thumbnail_url: Optional[str] = strawberry.field(description="URL to the auto-generated thumbnail (for images).")
    mime_type: str = strawberry.field(description="MIME type of the file (e.g., 'image/png').")
    size: int = strawberry.field(description="File size in bytes.")
    size_mb: float = strawberry.field(description="File size in megabytes.")
    file_type: str = strawberry.field(description="User-defined category (e.g., 'avatar', 'document').")
    width: Optional[int] = strawberry.field(description="Width of the image in pixels.")
    height: Optional[int] = strawberry.field(description="Height of the image in pixels.")
    created_at: str = strawberry.field(description="Timestamp of when the file was uploaded.")

    @staticmethod
    def from_model(file_model: FileModel) -> "FileType":
        return FileType(
            id=file_model.id, filename=file_model.filename, url=file_model.url,
            thumbnail_url=file_model.thumbnail_url, mime_type=file_model.mime_type,
            size=file_model.size, size_mb=file_model.size_mb, file_type=file_model.file_type,
            width=file_model.width, height=file_model.height, created_at=file_model.created_at.isoformat(),
        )

# ============================================================================
# Inputs
# ============================================================================

@strawberry.input(description="Input for uploading a generic file.")
class UploadFileInput:
    file: Upload = strawberry.field(description="The file to upload.")
    file_type: str = strawberry.field(description="A category for the file (e.g., 'avatar', 'attachment').")
    entity_type: Optional[str] = strawberry.field(default=None, description="Optional entity type to associate with the file (e.g., 'concept').")
    entity_id: Optional[int] = strawberry.field(default=None, description="Optional entity ID to associate with the file.")

# ============================================================================
# Queries
# ============================================================================

@strawberry.type
class FileQuery:
    """GraphQL queries for retrieving file information."""

    @strawberry.field(description='''Get a list of files uploaded by the current user.

Example:
```graphql
query GetMyAvatars {
  myFiles(fileType: "avatar", limit: 10) {
    id
    filename
    url
    createdAt
  }
}
```
''')
    def my_files(self, info: Info, file_type: Optional[str] = None, limit: int = 50) -> List[FileType]:
        user = info.context.get("user")
        if not user: raise Exception("Authentication required")
        db: Session = info.context["db"]
        service = FileService(db)
        files = service.get_user_files(user.id, file_type, limit)
        return [FileType.from_model(f) for f in files]

    @strawberry.field(description="Get a single file by its ID. Users can only access their own files.")
    def file(self, info: Info, file_id: int) -> Optional[FileType]:
        user = info.context.get("user")
        if not user: raise Exception("Authentication required")
        db: Session = info.context["db"]
        service = FileService(db)
        file_model = service.get_file_by_id(file_id)
        if not file_model: return None
        if file_model.uploaded_by_id != user.id: raise Exception("Access denied")
        return FileType.from_model(file_model)

# ============================================================================
# Mutations
# ============================================================================

@strawberry.type
class FileMutation:
    """GraphQL mutations for file management."""

    @strawberry.mutation(description='''Upload a user avatar. The file is automatically associated with the current user\'s profile.

This mutation requires a multipart form-data request.

Example (using a GraphQL client):
```graphql
mutation UploadAvatar($file: Upload!) {
  uploadAvatar(file: $file) {
    id
    url
    thumbnailUrl
  }
}
```
Variables:
`{ "file": null }` (and then attach the file via the client\'s upload mechanism)
''')
    async def upload_avatar(self, info: Info, file: Upload) -> FileType:
        user = info.context.get("user")
        if not user: raise Exception("Authentication required")
        db: Session = info.context["db"]
        service = FileService(db)
        file_content = await file.read()

        try:
            result = service.upload_file(
                file_content=file_content, filename=file.filename, mime_type=file.content_type or "application/octet-stream",
                file_type="avatar", user_id=user.id, entity_type="profile", entity_id=user.id,
            )
            service.update_avatar(user.id, result["id"])
            file_model = service.get_file_by_id(result["id"])
            return FileType.from_model(file_model)
        except (ValueError, PermissionError) as e:
            raise Exception(str(e))

    @strawberry.mutation(description='''Upload a generic file with optional entity association.

This mutation requires a multipart form-data request.

Example (using a GraphQL client):
```graphql
mutation UploadDocument($file: Upload!) {
  uploadFile(input: {
    file: $file,
    fileType: "document",
    entityType: "concept",
    entityId: 123
  }) {
    id
    url
  }
}
```
''')
    async def upload_file(self, info: Info, input: UploadFileInput) -> FileType:
        user = info.context.get("user")
        if not user: raise Exception("Authentication required")
        db: Session = info.context["db"]
        service = FileService(db)
        file_content = await input.file.read()

        try:
            result = service.upload_file(
                file_content=file_content, filename=input.file.filename, mime_type=input.file.content_type or "application/octet-stream",
                file_type=input.file_type, user_id=user.id, entity_type=input.entity_type, entity_id=input.entity_id,
            )
            file_model = service.get_file_by_id(result["id"])
            return FileType.from_model(file_model)
        except (ValueError, PermissionError) as e:
            raise Exception(str(e))

    @strawberry.mutation(description='''Delete a file. Users can only delete their own files.

Example:
```graphql
mutation DeleteMyFile {
  deleteFile(fileId: 45)
}
```
''')
    def delete_file(self, info: Info, file_id: int) -> bool:
        user = info.context.get("user")
        if not user: raise Exception("Authentication required")
        db: Session = info.context["db"]
        service = FileService(db)
        try:
            return service.delete_file(file_id, user.id)
        except (ValueError, PermissionError) as e:
            raise Exception(str(e))
'''
