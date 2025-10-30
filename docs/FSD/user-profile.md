# User Profile Management

Complete user profile management with password change, email change, and account deletion.

## Features

- Update profile fields (firstName, lastName, bio, language, timezone)
- Change password with current password verification
- Change email address with verification
- Soft delete account with password confirmation
- Field validation (bio max 500 chars, names max 50 chars)
- Email notifications for profile changes
- Redis-based token storage for email changes

---

## GraphQL API

**See detailed documentation:**
- **Queries:** [docs/graphql/query/auth.md](../../graphql/query/auth.md)
- **Mutations:** [docs/graphql/mutation/profile.md](../../graphql/mutation/profile.md)

---

## Profile Fields

| Field | Type | Max Length | Description |
|-------|------|------------|-------------|
| `firstName` | String | 50 | First name |
| `lastName` | String | 50 | Last name |
| `bio` | String | 500 | Biography/description |
| `avatar` | String | - | Avatar URL (managed via file upload system) |
| `language` | String | 10 | Preferred language code (e.g., "en", "ru") |
| `timezone` | String | 50 | Timezone string (e.g., "UTC", "Europe/Moscow") |

---

## Security Features

### Password Change
- Requires current password verification
- Minimum 8 characters for new password
- Email notification sent on success

### Email Change
- Requires current password verification
- New email must be unique
- Verification email sent to new address
- Token valid for 24 hours
- Old email remains until confirmation

### Account Deletion
- Requires password confirmation
- Uses soft delete (can be restored by admin)
- All user data marked as deleted
- Can be restored by admin if needed

---

## Implementation

### Files

- **Service:** `auth/services/profile_service.py` - ProfileService with all business logic
- **GraphQL Schema:** `auth/schemas/user.py` - Mutations and queries
- **Model:** `auth/models/profile.py` - UserProfileModel (one-to-one with User)
- **Email Service:** `core/email_service.py` - Email templates for profile changes

### Database Relationships

```
User (1) ←→ (1) UserProfile
UserProfile (n) → (1) File (avatar)
```

---

## Validation Rules

- **First name:** max 50 characters
- **Last name:** max 50 characters
- **Bio:** max 500 characters
- **New password:** min 8 characters
- **Email:** must be unique and valid format
- **Language:** valid language code
- **Timezone:** valid timezone string

---

## Email Notifications

Profile changes trigger email notifications:

| Action | Email Sent | Template |
|--------|-----------|----------|
| Password changed | Yes | `password_changed.html` |
| Email change requested | Yes (to new email) | `email_change_verification.html` |
| Email changed | Yes (to both) | `email_changed.html` |
| Profile updated | Optional | `profile_updated.html` |

---

## Error Handling

### Common Errors

**Invalid current password:**
```json
{
  "message": "Current password is incorrect",
  "code": "INVALID_PASSWORD"
}
```

**Email already exists:**
```json
{
  "message": "Email address already in use",
  "code": "EMAIL_EXISTS"
}
```

**Validation error:**
```json
{
  "message": "Bio must be less than 500 characters",
  "code": "VALIDATION_ERROR"
}
```

---

## Usage Examples

### Update Profile

```python
from auth.services.profile_service import ProfileService

profile_service = ProfileService(db)
profile_service.update_profile(
    user_id=user.id,
    first_name="John",
    last_name="Doe",
    bio="Software engineer",
    language="en",
    timezone="UTC"
)
```

### Change Password

```python
profile_service.change_password(
    user_id=user.id,
    current_password="OldPass123!",
    new_password="NewPass123!"
)
```

### Change Email

```python
# Step 1: Request email change
profile_service.request_email_change(
    user_id=user.id,
    new_email="newemail@example.com",
    current_password="MyPass123!"
)

# Step 2: Confirm with token from email
profile_service.confirm_email_change(token="abc123")
```

---

## Testing

```python
def test_update_profile():
    # Update profile
    result = update_profile(
        user_id=1,
        first_name="John",
        bio="Test bio"
    )
    assert result.first_name == "John"

def test_change_password():
    # Change password
    result = change_password(
        user_id=1,
        current_password="OldPass123!",
        new_password="NewPass123!"
    )
    assert result.success is True

def test_email_change_flow():
    # Request email change
    request_email_change(
        user_id=1,
        new_email="new@example.com",
        current_password="Pass123!"
    )

    # Get token from email
    token = get_email_change_token()

    # Confirm email change
    result = confirm_email_change(token)
    assert result.success is True
```

---

## Best Practices

- **Always verify password** for sensitive operations
- **Send email notifications** for security-related changes
- **Use soft delete** for account deletion (allows recovery)
- **Validate all input** on server side
- **Rate limit** profile updates to prevent abuse
- **Log all changes** in audit trail
