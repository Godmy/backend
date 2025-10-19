from typing import List, Optional

import strawberry

from auth.dependencies.auth import get_required_user


@strawberry.type
class UserProfile:
    id: int
    first_name: Optional[str]
    last_name: Optional[str]
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
        from core.database import get_db

        current_user = await get_required_user(info)
        db = next(get_db())
        user = UserService.get_user_by_id(db, current_user["id"])

        if not user:
            raise Exception("User not found")

        profile_data = None
        if user.profile:
            profile_data = UserProfile(
                id=user.profile.id,
                first_name=user.profile.first_name,
                last_name=user.profile.last_name,
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
class UserMutation:
    @strawberry.mutation
    async def update_profile(
        self,
        info,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        language: Optional[str] = None,
        timezone: Optional[str] = None,
    ) -> User:
        from auth.models.profile import UserProfileModel
        from core.database import get_db

        current_user = await get_required_user(info)
        db = next(get_db())

        # Находим или создаем профиль
        profile = (
            db.query(UserProfileModel)
            .filter(UserProfileModel.user_id == current_user["id"])
            .first()
        )

        if not profile:
            profile = UserProfileModel(user_id=current_user["id"])
            db.add(profile)

        # Обновляем поля
        if first_name is not None:
            profile.first_name = first_name
        if last_name is not None:
            profile.last_name = last_name
        if language is not None:
            profile.language = language
        if timezone is not None:
            profile.timezone = timezone

        db.commit()
        db.refresh(profile)

        # Возвращаем обновленного пользователя
        user_query = UserQuery()
        return await user_query.me(info)
