# File Upload Mutations

**Required:** Authorization header

## Upload Avatar

Upload avatar image (automatically updates user profile).

```graphql
mutation UploadAvatar($file: Upload!) {
  uploadAvatar(file: $file) {
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

**Validation:**
- Max size: 5MB
- Allowed types: PNG, JPG, GIF, WEBP
- Automatically generates 256x256 thumbnail
- Updates user profile avatar URL

**Using with GraphQL clients:**

```javascript
// JavaScript example with Apollo Client
const [uploadAvatar] = useMutation(UPLOAD_AVATAR_MUTATION);

const handleUpload = async (file) => {
  await uploadAvatar({
    variables: { file }
  });
};
```

---

## Upload Generic File

Upload any file with custom metadata.

```graphql
mutation UploadFile(
  $file: Upload!
  $fileType: String!
  $entityType: String
  $entityId: Int
) {
  uploadFile(
    file: $file
    fileType: $fileType
    entityType: $entityType
    entityId: $entityId
  ) {
    id
    filename
    url
    thumbnailUrl
    sizeMb
    createdAt
  }
}
```

**Parameters:**
- `file` - File upload (required)
- `fileType` - Category: avatar, image, document, etc. (required)
- `entityType` - Related entity type: concept, user, etc. (optional)
- `entityId` - Related entity ID (optional)

**Validation:**
- Max size: 10MB (5MB for avatars)
- Allowed types: PNG, JPG, GIF, WEBP
- Automatically generates thumbnails for images

---

## Delete File

Delete uploaded file.

```graphql
mutation DeleteFile($fileId: Int!) {
  deleteFile(fileId: $fileId)  # Returns boolean
}
```

**Security:**
- Can only delete your own files (unless admin)
- Deletes both original and thumbnail
- Removes file from filesystem and database

---

## Configuration

```env
# .env
UPLOAD_DIR=uploads
```

**Directory permissions:**
- Must be writable by application
- Files served via `/uploads/{filename}` endpoint

---

## Security Features

- Filename sanitization (prevents path traversal)
- MIME type validation
- Size limits enforced
- User ownership verification
- Automatic cleanup on user deletion

---

## Implementation

- `core/models/file.py` - FileModel
- `core/schemas/file.py` - GraphQL API
- `core/services/file_service.py` - Business logic and validation
- `core/file_storage.py` - FileStorageService (filesystem operations)
- `app.py` - `/uploads/{filename:path}` endpoint
