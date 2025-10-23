# File Upload System

The application supports secure file uploads with automatic thumbnail generation and validation.

## Features

- Secure file storage with sanitized filenames
- Automatic thumbnail generation (256x256) for images
- Size validation (5MB for avatars, 10MB for other files)
- MIME type validation (PNG, JPG, GIF, WEBP)
- Path traversal protection
- Integration with user profiles (avatars)

## Directory Structure

```
uploads/
├── 20250116_abc123def456.png  # Original files
└── thumbnails/
    └── 20250116_abc123def456.png  # Auto-generated thumbnails
```

## GraphQL API

- **Queries:** [docs/graphql/query/file.md](../graphql/query/file.md)
- **Mutations:** [docs/graphql/mutation/file.md](../graphql/mutation/file.md)

## Implementation Details

- `core/models/file.py` - File model with metadata
- `core/file_storage.py` - FileStorageService for filesystem operations
- `core/services/file_service.py` - Business logic and validation
- `core/schemas/file.py` - GraphQL API
- `app.py` - `/uploads/{filename:path}` endpoint for serving files

## Configuration

```env
# .env
UPLOAD_DIR=uploads
```

## File Types

The system supports different file type categories:
- **avatar** - User profile avatars (5MB limit)
- **attachment** - Generic file attachments (10MB limit)
- **image** - Image files with thumbnail generation
- **document** - Document files (PDF, DOCX, etc.)

## Validation

### Size Limits
- Avatar files: 5MB maximum
- Other files: 10MB maximum

### MIME Types
- **Images:** PNG, JPG, JPEG, GIF, WEBP
- **Documents:** PDF, DOCX, XLSX, TXT

### Security
- Filename sanitization to prevent path traversal
- MIME type verification
- Virus scanning (optional, configurable)
- User ownership verification for file operations

## Thumbnail Generation

Thumbnails are automatically generated for image files:
- Size: 256x256 pixels
- Maintains aspect ratio
- Stored in `uploads/thumbnails/` directory
- Same filename as original
- Generated on upload

## Usage Example

```python
from core.services.file_service import FileService

file_service = FileService(db)

# Upload avatar
file = await file_service.upload_avatar(
    user=current_user,
    file_data=uploaded_file,
    filename="avatar.png"
)

# Get user files
files = file_service.get_user_files(
    user_id=current_user.id,
    file_type="avatar",
    limit=10
)

# Delete file
file_service.delete_file(
    file_id=123,
    user_id=current_user.id
)
```

## Testing

See [TESTING_GUIDE.md](../../TESTING_GUIDE.md) for full testing guide.

### Test file uploads:
```bash
# Upload avatar via GraphQL
curl -X POST http://localhost:8000/graphql \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F operations='{"query":"mutation($file: Upload!){uploadAvatar(file:$file){id filename url}}","variables":{"file":null}}' \
  -F map='{"0":["variables.file"]}' \
  -F 0=@avatar.png
```

## Error Handling

The system handles various error scenarios:
- File too large: Returns error with size limit
- Invalid MIME type: Returns list of allowed types
- Disk space full: Returns server error
- Permission denied: Returns authorization error
- File not found: Returns 404 error
