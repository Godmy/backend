# File Upload Queries

**Required:** Authorization header

## Get My Files

Get list of files uploaded by current user.

```graphql
query MyFiles {
  myFiles(fileType: "avatar", limit: 10) {
    id
    filename
    url
    thumbnailUrl
    mimeType
    size
    sizeMb
    fileType
    width
    height
    createdAt
  }
}
```

**Filter options:**
- `fileType` - Filter by file type (avatar, document, image, etc.)
- `limit` - Number of results to return

---

## File Metadata

File model includes:
- `id` - Unique identifier
- `filename` - Sanitized filename on disk
- `url` - Public URL to access file
- `thumbnailUrl` - URL to thumbnail (for images)
- `mimeType` - MIME type (e.g., "image/png")
- `size` - File size in bytes
- `sizeMb` - File size in megabytes
- `fileType` - Category (avatar, image, document, etc.)
- `width`, `height` - Image dimensions (null for non-images)
- `entityType`, `entityId` - Optional link to related entity
- `uploadedById` - User who uploaded the file
- `createdAt`, `updatedAt` - Timestamps

---

## File Storage

**Directory structure:**
```
uploads/
├── 20250116_abc123def456.png  # Original files
└── thumbnails/
    └── 20250116_abc123def456.png  # Auto-generated thumbnails
```

**Features:**
- Sanitized filenames (prevents path traversal)
- Automatic thumbnail generation (256x256) for images
- Indexed by user and file type

---

## Accessing Files

Files are served via HTTP endpoint:
```
GET /uploads/{filename}
```

Example:
```
http://localhost:8000/uploads/20250116_abc123def456.png
```

---

## Implementation

- `core/models/file.py` - FileModel
- `core/schemas/file.py` - GraphQL API
- `core/services/file_service.py` - Business logic
- `core/file_storage.py` - FileStorageService
- `app.py` - `/uploads/{filename:path}` endpoint
