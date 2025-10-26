from typing import List, Optional

import strawberry

from auth.dependencies.auth import get_required_user


@strawberry.type
class UserProfile:
    id: int
    first_name: Optional[str]
    last_name: Optional[str]
    bio: Optional[str]
    avatar: Optional[str]
    language: str
    timezone: str


@strawberry.type
class User:
    id: int
    username: str
    email: str
    is_active: bool
    is_verified: bool
    profile: Optional[UserProfile]


@strawberry.type
class UserQuery:
    @strawberry.field
    async def me(self, info) -> User:
        from auth.services.user_service import UserService

        current_user = await get_required_user(info)
        # Use DB session from context (no connection leak)
        db = info.context["db"]
        user = UserService.get_user_by_id(db, current_user["id"])

        if not user:
            raise Exception("User not found")

        profile_data = None
        if user.profile:
            profile_data = UserProfile(
                id=user.profile.id,
                first_name=user.profile.first_name,
                last_name=user.profile.last_name,
                bio=user.profile.bio,
                avatar=user.profile.avatar,
                language=user.profile.language,
                timezone=user.profile.timezone,
            )

        return User(
            id=user.id,
            username=user.username,
            email=user.email,
            is_active=user.is_active,
            is_verified=user.is_verified,
            profile=profile_data,
        )


@strawberry.type
class SuccessResponse:
    """Generic success response"""

    success: bool
    message: str


@strawberry.type
class UserMutation:
    @strawberry.mutation
    async def update_profile(
        self,
        info,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        bio: Optional[str] = None,
        language: Optional[str] = None,
        timezone: Optional[str] = None,
    ) -> User:
        """
        Update user profile fields.

        Args:
            first_name: First name (max 50 chars)
            last_name: Last name (max 50 chars)
            bio: Biography (max 500 chars)
            language: Language code (e.g., "en", "ru")
            timezone: Timezone (e.g., "UTC", "Europe/Moscow")

        Returns:
            Updated user with profile

        Example:
            mutation {
              updateProfile(
                firstName: "John"
                lastName: "Doe"
                bio: "Software engineer"
                language: "en"
                timezone: "UTC"
              ) {
                id
                profile { firstName lastName bio }
              }
            }
        """
        from auth.services.profile_service import ProfileService

        current_user = await get_required_user(info)
        # Use DB session from context (no connection leak)
        db = info.context["db"]

        try:
            ProfileService.update_profile(
                db,
                current_user["id"],
                first_name=first_name,
                last_name=last_name,
                bio=bio,
                language=language,
                timezone=timezone,
            )

            # Return updated user
            user_query = UserQuery()
            return await user_query.me(info)

        except ValueError as e:
            raise Exception(str(e))

    @strawberry.mutation
    async def change_password(
        self, info, current_password: str, new_password: str
    ) -> SuccessResponse:
        """
        Change user password.

        Requires current password for verification.

        Args:
            current_password: Current password
            new_password: New password (min 8 characters)

        Returns:
            Success response

        Example:
            mutation {
              changePassword(
                currentPassword: "OldPass123!"
                newPassword: "NewPass123!"
              ) {
                success
                message
              }
            }
        """
        from auth.services.profile_service import ProfileService

        current_user = await get_required_user(info)
        # Use DB session from context (no connection leak)
        db = info.context["db"]

        try:
            ProfileService.change_password(
                db, current_user["id"], current_password, new_password
            )

            return SuccessResponse(
                success=True, message="Password changed successfully"
            )

        except ValueError as e:
            raise Exception(str(e))

    @strawberry.mutation
    async def request_email_change(
        self, info, new_email: str, current_password: str
    ) -> SuccessResponse:
        """
        Request email address change.

        Sends verification email to new address.

        Args:
            new_email: New email address
            current_password: Current password for verification

        Returns:
            Success response

        Example:
            mutation {
              requestEmailChange(
                newEmail: "newemail@example.com"
                currentPassword: "MyPass123!"
              ) {
                success
                message
              }
            }
        """
        from auth.services.profile_service import ProfileService
        from core.email_service import email_service

        current_user = await get_required_user(info)
        # Use DB session from context (no connection leak)
        db = info.context["db"]

        try:
            token = ProfileService.initiate_email_change(
                db, current_user["id"], new_email, current_password
            )

            # Send verification email
            email_service.send_email_change_verification(
                to_email=new_email, username=current_user["username"], token=token
            )

            return SuccessResponse(
                success=True,
                message=f"Verification email sent to {new_email}. Please check your inbox.",
            )

        except ValueError as e:
            raise Exception(str(e))

    @strawberry.mutation
    async def confirm_email_change(self, token: str) -> SuccessResponse:
        """
        Confirm email change with verification token.

        Args:
            token: Verification token from email

        Returns:
            Success response

        Example:
            mutation {
              confirmEmailChange(token: "verification_token_here") {
                success
                message
              }
            }
        """
        from auth.services.profile_service import ProfileService

        # Use DB session from context (no connection leak)
        db = info.context["db"]

        try:
            ProfileService.confirm_email_change(db, token)

            return SuccessResponse(
                success=True, message="Email changed successfully"
            )

        except ValueError as e:
            raise Exception(str(e))

    @strawberry.mutation
    async def delete_account(self, info, password: str) -> SuccessResponse:
        """
        Delete user account (soft delete).

        Account can be restored by admin within retention period.

        Args:
            password: Password for verification

        Returns:
            Success response

        Example:
            mutation {
              deleteAccount(password: "MyPass123!") {
                success
                message
              }
            }
        """
        from auth.services.profile_service import ProfileService

        current_user = await get_required_user(info)
        # Use DB session from context (no connection leak)
        db = info.context["db"]

        try:
            ProfileService.delete_account(db, current_user["id"], password)

            return SuccessResponse(
                success=True,
                message="Account deleted successfully. You will be logged out.",
            )

        except ValueError as e:
            raise Exception(str(e))
