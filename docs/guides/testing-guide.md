# Testing Guide - МультиПУЛЬТ Backend

This guide provides instructions for testing the newly implemented File Upload and Audit Logging features.

## Quick Start

```bash
# Start all services in Docker
docker-compose -f docker-compose.dev.yml up

# Services will be available at:
# - GraphQL API: http://localhost:8000/graphql
# - Health Check: http://localhost:8000/health
# - MailPit UI: http://localhost:8025
```

## Testing with GraphQL Playground

### 1. Open GraphQL Playground

Navigate to `http://localhost:8000/graphql` in your browser.

### 2. Authentication

First, you need to login to get an access token:

```graphql
mutation Login {
  login(input: {
    username: "admin"
    password: "Admin123!"
  }) {
    accessToken
    refreshToken
    tokenType
  }
}
```

**Response:**
```json
{
  "data": {
    "login": {
      "accessToken": "eyJhbGciOiJIUzI1NiIs...",
      "refreshToken": "eyJhbGciOiJIUzI1NiIs...",
      "tokenType": "bearer"
    }
  }
}
```

**Set Authorization Header:**

In GraphQL Playground, click on "HTTP HEADERS" at the bottom and add:

```json
{
  "Authorization": "Bearer YOUR_ACCESS_TOKEN_HERE"
}
```

Replace `YOUR_ACCESS_TOKEN_HERE` with the actual token from the login response.

## Testing Audit Logging

### 1. View Your Audit Logs

```graphql
query MyAuditLogs {
  myAuditLogs(limit: 10) {
    logs {
      id
      action
      entityType
      entityId
      description
      status
      createdAt
    }
    total
    hasMore
  }
}
```

**Expected Response:**
```json
{
  "data": {
    "myAuditLogs": {
      "logs": [
        {
          "id": 1,
          "action": "login",
          "entityType": null,
          "entityId": null,
          "description": "User logged in",
          "status": "success",
          "createdAt": "2025-01-16T10:30:00"
        }
      ],
      "total": 1,
      "hasMore": false
    }
  }
}
```

### 2. View All Audit Logs (Admin Only)

```graphql
query AuditLogs {
  auditLogs(
    filters: {
      action: "login"
      status: "success"
    }
    limit: 20
    offset: 0
  ) {
    logs {
      id
      userId
      action
      entityType
      entityId
      description
      ipAddress
      userAgent
      status
      createdAt
    }
    total
    hasMore
  }
}
```

### 3. View User Activity Statistics

```graphql
query UserActivity {
  userActivity(days: 7) {
    action
    count
  }
}
```

**Expected Response:**
```json
{
  "data": {
    "userActivity": [
      {
        "action": "login",
        "count": 5
      },
      {
        "action": "profile_update",
        "count": 2
      }
    ]
  }
}
```

## Testing File Upload

### Method 1: Using GraphQL Playground (Recommended)

**Note:** GraphQL Playground has built-in support for file uploads.

#### Upload Avatar

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

**Steps:**
1. Click on "Query Variables" section
2. Add file variable:
   ```json
   {
     "file": null
   }
   ```
3. The playground should show a file upload button
4. Select an image file (PNG, JPG, GIF - max 5MB)
5. Click "Execute Query"

**Expected Response:**
```json
{
  "data": {
    "uploadAvatar": {
      "id": 1,
      "filename": "avatar.png",
      "url": "/uploads/20250116_abc123def456.png",
      "thumbnailUrl": "/uploads/thumbnails/20250116_abc123def456.png",
      "mimeType": "image/png",
      "size": 1048576,
      "sizeMb": 1.0,
      "fileType": "avatar",
      "width": 1024,
      "height": 768,
      "createdAt": "2025-01-16T10:30:00"
    }
  }
}
```

#### Upload Generic File

```graphql
mutation UploadFile($input: UploadFileInput!) {
  uploadFile(input: $input) {
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

**Query Variables:**
```json
{
  "input": {
    "file": null,
    "fileType": "image",
    "entityType": "concept",
    "entityId": 1
  }
}
```

### Method 2: Using cURL

```bash
# Get access token first
TOKEN=$(curl -s -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"mutation { login(input: {username: \"admin\", password: \"Admin123!\"}) { accessToken } }"}' \
  | jq -r '.data.login.accessToken')

# Upload file (multipart/form-data)
curl -X POST http://localhost:8000/graphql \
  -H "Authorization: Bearer $TOKEN" \
  -F operations='{"query":"mutation($file: Upload!) { uploadAvatar(file: $file) { id filename url } }","variables":{"file":null}}' \
  -F map='{"0":["variables.file"]}' \
  -F 0=@/path/to/your/image.png
```

### Method 3: Using Python (requests library)

```python
import requests

# 1. Login
response = requests.post(
    "http://localhost:8000/graphql",
    json={
        "query": """
            mutation {
                login(input: {username: "admin", password: "Admin123!"}) {
                    accessToken
                }
            }
        """
    }
)
token = response.json()["data"]["login"]["accessToken"]

# 2. Upload file
with open("test_image.png", "rb") as f:
    files = {
        'operations': (None, '{"query":"mutation($file: Upload!) { uploadAvatar(file: $file) { id filename url } }","variables":{"file":null}}'),
        'map': (None, '{"0":["variables.file"]}'),
        '0': ('test_image.png', f, 'image/png')
    }

    response = requests.post(
        "http://localhost:8000/graphql",
        headers={"Authorization": f"Bearer {token}"},
        files=files
    )

    print(response.json())
```

### Verify File Upload

After uploading a file, you can:

1. **View uploaded files:**
   ```graphql
   query MyFiles {
     myFiles(fileType: "avatar", limit: 10) {
       id
       filename
       url
       thumbnailUrl
       sizeMb
       createdAt
     }
   }
   ```

2. **Access the file directly:**
   - Original: `http://localhost:8000/uploads/20250116_abc123def456.png`
   - Thumbnail: `http://localhost:8000/uploads/thumbnails/20250116_abc123def456.png`

3. **Check the uploads directory:**
   ```bash
   # List uploaded files
   ls -lh uploads/

   # List thumbnails
   ls -lh uploads/thumbnails/
   ```

### Delete File

```graphql
mutation DeleteFile($fileId: Int!) {
  deleteFile(fileId: $fileId)
}
```

**Query Variables:**
```json
{
  "fileId": 1
}
```

## Testing Scenarios

### Scenario 1: User Registration & Login Flow

1. **Register new user:**
   ```graphql
   mutation {
     register(input: {
       username: "testuser"
       email: "test@example.com"
       password: "TestPass123!"
     }) {
       accessToken
     }
   }
   ```

2. **Check audit logs:**
   - Should see "register" action in myAuditLogs

3. **Login:**
   ```graphql
   mutation {
     login(input: {
       username: "testuser"
       password: "TestPass123!"
     }) {
       accessToken
     }
   }
   ```

4. **Check audit logs again:**
   - Should now see both "register" and "login" actions

### Scenario 2: File Upload & Management

1. **Upload avatar**
2. **Check myFiles** - should see the uploaded file
3. **Check uploads directory** - file and thumbnail should exist
4. **Delete file**
5. **Check myFiles** - file should be gone
6. **Check uploads directory** - file and thumbnail should be deleted

### Scenario 3: Admin Monitoring

1. **Login as admin**
2. **View all audit logs:**
   - Filter by action (login, register, upload)
   - Filter by user
   - Check pagination

3. **View user activity:**
   - Get statistics for specific user
   - Get statistics for all users (if admin)

## Troubleshooting

### 1. "Authentication required" error

**Problem:** GraphQL returns "Authentication required"

**Solution:** Make sure you've set the Authorization header:
```json
{
  "Authorization": "Bearer your_access_token_here"
}
```

### 2. File upload fails with 400 error

**Problem:** File upload returns HTTP 400

**Possible causes:**
- File too large (max 5MB for avatars, 10MB for other files)
- Invalid MIME type
- Missing authorization header
- Strawberry GraphQL file upload not properly configured

**Solution:**
- Check file size
- Use supported image formats (PNG, JPG, GIF)
- Verify Authorization header is set

### 3. Uploaded file not accessible

**Problem:** Cannot access file via `/uploads/` endpoint

**Solution:**
- Check uploads directory permissions
- Verify file was actually saved (check `uploads/` directory)
- Check filename in database matches file on disk

### 4. Thumbnails not generated

**Problem:** `hasThumbnail` is false or thumbnail_url is null

**Possible causes:**
- Pillow not installed
- Invalid image format
- Image processing error

**Solution:**
- Check application logs: `docker logs templates_app_dev`
- Verify Pillow is installed: `docker exec templates_app_dev pip list | grep Pillow`

## Database Inspection

You can inspect the database directly to verify data:

```bash
# Connect to PostgreSQL
docker exec -it templates_db_dev psql -U template_user -d templates

# Check files table
\d files
SELECT id, filename, file_type, size, uploaded_by, created_at FROM files;

# Check audit_logs table
\d audit_logs
SELECT id, user_id, action, entity_type, status, created_at FROM audit_logs ORDER BY created_at DESC LIMIT 10;

# Exit
\q
```

## API Documentation

For complete API documentation, export the GraphQL schema:

```bash
# Export schema
strawberry export-schema core.schemas.schema:schema > schema.graphql

# View in browser
open schema.graphql
```

## Test Accounts

When `SEED_DATABASE=true`, the following test accounts are available:

| Username  | Password       | Role      |
|-----------|----------------|-----------|
| admin     | Admin123!      | Admin     |
| moderator | Moderator123!  | Moderator |
| editor    | Editor123!     | Editor    |
| testuser  | User123!       | User      |

All accounts are pre-verified (no email verification required).

## Next Steps

After successful testing:

1. Update BACKLOG.md - mark P0 tasks as completed
2. Write integration tests in `tests/` directory
3. Add monitoring and alerting for file uploads
4. Implement file size limits per user/role
5. Add file type restrictions
6. Implement file virus scanning (ClamAV)
7. Add file storage analytics (total size, count per user)

## Support

If you encounter any issues:

1. Check application logs: `docker logs templates_app_dev`
2. Check database logs: `docker logs templates_db_dev`
3. Check Redis logs: `docker logs templates_redis`
4. Review the code in:
   - `core/models/file.py`
   - `core/services/file_service.py`
   - `core/schemas/file.py`
   - `core/models/audit_log.py`
   - `core/services/audit_service.py`
   - `core/schemas/audit.py`
