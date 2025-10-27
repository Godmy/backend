"""
GraphQL schemas for user and profile management.
"""

from typing import Optional
import strawberry
from strawberry.types import Info

from auth.dependencies.auth import get_required_user

# ============================================================================
# Types
# ============================================================================

@strawberry.type(description="Represents a user's profile information.")
class UserProfile:
    id: int
    first_name: Optional[str]
    last_name: Optional[str]
    bio: Optional[str] = strawberry.field(description="A short biography or description.")
    avatar: Optional[str] = strawberry.field(description="URL of the user's avatar image.")
    language: str = strawberry.field(description="The user's preferred language code (e.g., 'en').")
    timezone: str = strawberry.field(description="The user's timezone (e.g., 'UTC').")

@strawberry.type(description="Represents a user account.")
class User:
    id: int
    username: str
    email: str
    is_active: bool = strawberry.field(description="Indicates if the user account is active.")
    is_verified: bool = strawberry.field(description="Indicates if the user's email has been verified.")
    profile: Optional[UserProfile]

@strawberry.type(description="A generic response indicating the success or failure of a mutation.")
class SuccessResponse:
    success: bool
    message: str

# ============================================================================
# Queries
# ============================================================================

@strawberry.type
class UserQuery:
    @strawberry.field(description="""Get information about the currently authenticated user.

**Requires authentication.**

Example:
```graphql
query GetCurrentUser {
  me {
    id
    username
    email
    profile {
      firstName
      lastName
      language
    }
  }
}
```
""")
    async def me(self, info: Info) -> User:
        from auth.services.user_service import UserService
        current_user_dict = await get_required_user(info)
        db = info.context["db"]
        user = UserService.get_user_by_id(db, current_user_dict["id"])
        if not user: raise Exception("User not found")

        profile_data = UserProfile(
            id=user.profile.id, first_name=user.profile.first_name, last_name=user.profile.last_name,
            bio=user.profile.bio, avatar=user.profile.avatar, language=user.profile.language,
            timezone=user.profile.timezone
        ) if user.profile else None

        return User(
            id=user.id, username=user.username, email=user.email, is_active=user.is_active,
            is_verified=user.is_verified, profile=profile_data
        )

# ============================================================================
# Mutations
# ============================================================================

@strawberry.type
class UserMutation:
    @strawberry.mutation(description="""Update the current user's profile.

**Requires authentication.**

Example:
```graphql
mutation UpdateMyProfile {
  updateProfile(
    firstName: "John"
    lastName: "Doe"
    bio: "Software Engineer"
    language: "en"
  ) {
    id
    profile { firstName bio }
  }
}
```
""")
    async def update_profile(
        self, info: Info, first_name: Optional[str] = None, last_name: Optional[str] = None,
        bio: Optional[str] = None, language: Optional[str] = None, timezone: Optional[str] = None
    ) -> User:
        from auth.services.profile_service import ProfileService
        current_user_dict = await get_required_user(info)
        db = info.context["db"]
        try:
            ProfileService.update_profile(
                db, current_user_dict["id"], first_name=first_name, last_name=last_name,
                bio=bio, language=language, timezone=timezone
            )
            return await UserQuery().me(info)
        except ValueError as e:
            raise Exception(str(e))

    @strawberry.mutation(description="""Change the current user's password.

**Requires authentication.**

Example:
```graphql
mutation ChangeMyPassword {
  changePassword(
    currentPassword: "OldPassword123!"
    newPassword: "NewSecurePassword456!"
  ) {
    success
    message
  }
}
```
""")
    async def change_password(self, info: Info, current_password: str, new_password: str) -> SuccessResponse:
        from auth.services.profile_service import ProfileService
        current_user_dict = await get_required_user(info)
        db = info.context["db"]
        try:
            ProfileService.change_password(db, current_user_dict["id"], current_password, new_password)
            return SuccessResponse(success=True, message="Password changed successfully")
        except ValueError as e:
            raise Exception(str(e))

    @strawberry.mutation(description="""Initiate an email address change for the current user.

Sends a verification link to the new email address.

**Requires authentication.**

Example:
```graphql
mutation StartEmailChange {
  requestEmailChange(
    newEmail: "john.doe@new-email.com"
    currentPassword: "MyCurrentPassword123!"
  ) {
    success
    message
  }
}
```
""")
    async def request_email_change(self, info: Info, new_email: str, current_password: str) -> SuccessResponse:
        from auth.services.profile_service import ProfileService
        from core.email_service import email_service
        current_user_dict = await get_required_user(info)
        db = info.context["db"]
        try:
            token = ProfileService.initiate_email_change(db, current_user_dict["id"], new_email, current_password)
            email_service.send_email_change_verification(
                to_email=new_email, username=current_user_dict["username"], token=token
            )
            return SuccessResponse(success=True, message=f"Verification email sent to {new_email}.")
        except ValueError as e:
            raise Exception(str(e))

    @strawberry.mutation(description="""Confirm an email address change using the token from the verification email.

Example:
```graphql
mutation CompleteEmailChange {
  confirmEmailChange(token: "the_token_from_the_email_link") {
    success
    message
  }
}
```
""")
    async def confirm_email_change(self, info: Info, token: str) -> SuccessResponse:
        from auth.services.profile_service import ProfileService
        db = info.context["db"]
        try:
            ProfileService.confirm_email_change(db, token)
            return SuccessResponse(success=True, message="Email changed successfully")
        except ValueError as e:
            raise Exception(str(e))

    @strawberry.mutation(description="""Soft-delete the current user's account.

This is a reversible action. The account can be restored by an administrator.

**Requires authentication.**

Example:
```graphql
mutation DeleteMyAccount {
  deleteAccount(password: "MyCurrentPassword123!") {
    success
    message
  }
}
```
""")
    async def delete_account(self, info: Info, password: str) -> SuccessResponse:
        from auth.services.profile_service import ProfileService
        current_user_dict = await get_required_user(info)
        db = info.context["db"]
        try:
            ProfileService.delete_account(db, current_user_dict["id"], password)
            return SuccessResponse(success=True, message="Account deleted successfully. You will be logged out.")
        except ValueError as e:
            raise Exception(str(e))
