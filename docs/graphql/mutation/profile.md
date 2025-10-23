# User Profile Mutations

## Update Profile

Update user profile fields.

**Required:** Authorization header

```graphql
mutation UpdateProfile {
  updateProfile(
    firstName: "John"
    lastName: "Doe"
    bio: "Software engineer passionate about GraphQL"
    language: "en"
    timezone: "UTC"
  ) {
    id
    profile {
      firstName
      lastName
      bio
      language
      timezone
    }
  }
}
```

**Validation rules:**
- First name: max 50 characters
- Last name: max 50 characters
- Bio: max 500 characters

---

## Change Password

Change user password (requires current password verification).

**Required:** Authorization header

```graphql
mutation ChangePassword {
  changePassword(
    currentPassword: "OldPass123!"
    newPassword: "NewPass123!"
  ) {
    success
    message
  }
}
```

**Validation:**
- New password: min 8 characters
- Current password must be correct

**Email notification:** Sent automatically on success

---

## Request Email Change

Request email address change (sends verification email to new address).

**Required:** Authorization header

```graphql
mutation RequestEmailChange {
  requestEmailChange(
    newEmail: "newemail@example.com"
    currentPassword: "MyPass123!"
  ) {
    success
    message
  }
}
```

**Security:**
- Requires current password verification
- New email must be unique
- Token valid for 24 hours

---

## Confirm Email Change

Confirm email change using token from verification email.

```graphql
mutation ConfirmEmailChange {
  confirmEmailChange(token: "token_from_email") {
    success
    message
  }
}
```

---

## Delete Account

Soft delete user account (requires password confirmation).

**Required:** Authorization header

```graphql
mutation DeleteAccount {
  deleteAccount(password: "MyPass123!") {
    success
    message
  }
}
```

**Notes:**
- Uses soft delete (can be restored by admin)
- Requires password verification
- Account marked as deleted, not permanently removed

---

## Profile Fields

Available profile fields:
- `firstName` - First name (max 50 characters)
- `lastName` - Last name (max 50 characters)
- `bio` - Biography/description (max 500 characters)
- `avatar` - Avatar URL (managed via file upload system)
- `language` - Preferred language code (e.g., "en", "ru")
- `timezone` - Timezone string (e.g., "UTC", "Europe/Moscow")

**Implementation:**
- `auth/services/profile_service.py` - ProfileService
- `auth/models/profile.py` - UserProfileModel
- `core/email_service.py` - Email notifications
