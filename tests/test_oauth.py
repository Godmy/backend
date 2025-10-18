"""
OAuth Service Tests

Tests for Google and Telegram OAuth authentication
"""

import pytest
import hashlib
import hmac
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session

from auth.services.oauth_service import OAuthService
from auth.models.oauth import OAuthConnectionModel
from auth.models.user import UserModel


# Test Data
MOCK_GOOGLE_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjE..."
MOCK_GOOGLE_USER_DATA = {
    "provider_user_id": "google_123456789",
    "email": "test@gmail.com",
    "email_verified": True,
    "name": "Test User",
    "given_name": "Test",
    "family_name": "User",
    "picture": "https://example.com/photo.jpg",
    "locale": "en"
}

MOCK_TELEGRAM_DATA = {
    "id": "123456789",
    "auth_date": "1640000000",
    "hash": "correct_hash",
    "first_name": "John",
    "last_name": "Doe",
    "username": "johndoe",
    "photo_url": "https://t.me/i/userpic/photo.jpg"
}


@pytest.mark.unit
class TestGoogleOAuth:
    """Test Google OAuth functionality"""

    @pytest.mark.asyncio
    async def test_verify_google_token_success(self):
        """Test successful Google token verification"""
        with patch('auth.services.oauth_service.google_id_token') as mock_id_token:
            # Mock Google's token verification
            mock_id_token.verify_oauth2_token.return_value = {
                "sub": "google_123456789",
                "email": "test@gmail.com",
                "email_verified": True,
                "name": "Test User",
                "given_name": "Test",
                "family_name": "User",
                "picture": "https://example.com/photo.jpg",
                "locale": "en"
            }

            with patch.dict('os.environ', {'GOOGLE_CLIENT_ID': 'test_client_id'}):
                result = await OAuthService.verify_google_token(MOCK_GOOGLE_TOKEN)

            assert result is not None
            assert result["provider_user_id"] == "google_123456789"
            assert result["email"] == "test@gmail.com"
            assert result["email_verified"] is True

    @pytest.mark.asyncio
    async def test_verify_google_token_invalid(self):
        """Test Google token verification with invalid token"""
        with patch('auth.services.oauth_service.google_id_token') as mock_id_token:
            # Mock verification failure
            mock_id_token.verify_oauth2_token.side_effect = ValueError("Invalid token")

            with patch.dict('os.environ', {'GOOGLE_CLIENT_ID': 'test_client_id'}):
                result = await OAuthService.verify_google_token("invalid_token")

            assert result is None

    @pytest.mark.asyncio
    async def test_verify_google_token_no_client_id(self):
        """Test Google token verification without client ID configured"""
        with patch.dict('os.environ', {}, clear=True):
            result = await OAuthService.verify_google_token(MOCK_GOOGLE_TOKEN)

        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_with_google_new_user(self, db_session: Session):
        """Test Google OAuth authentication with new user"""
        with patch('auth.services.oauth_service.OAuthService.verify_google_token') as mock_verify:
            mock_verify.return_value = MOCK_GOOGLE_USER_DATA

            result, error = await OAuthService.authenticate_with_google(
                db_session,
                MOCK_GOOGLE_TOKEN
            )

            assert error is None
            assert result is not None
            assert "access_token" in result
            assert "refresh_token" in result
            assert result["token_type"] == "bearer"

            # Verify user was created
            user = result["user"]
            assert user.email == "test@gmail.com"
            assert user.is_verified is True

            # Verify OAuth connection was created
            oauth_conn = db_session.query(OAuthConnectionModel).filter_by(
                provider="google",
                provider_user_id="google_123456789"
            ).first()
            assert oauth_conn is not None
            assert oauth_conn.user_id == user.id

    @pytest.mark.asyncio
    async def test_authenticate_with_google_existing_oauth(self, db_session: Session):
        """Test Google OAuth authentication with existing OAuth connection"""
        # Create existing user and OAuth connection
        user = UserModel(
            username="existing_user",
            email="test@gmail.com",
            password_hash="hash",
            is_verified=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        oauth_conn = OAuthConnectionModel(
            user_id=user.id,
            provider="google",
            provider_user_id="google_123456789",
            provider_email="test@gmail.com"
        )
        db_session.add(oauth_conn)
        db_session.commit()

        with patch('auth.services.oauth_service.OAuthService.verify_google_token') as mock_verify:
            mock_verify.return_value = MOCK_GOOGLE_USER_DATA

            result, error = await OAuthService.authenticate_with_google(
                db_session,
                MOCK_GOOGLE_TOKEN
            )

            assert error is None
            assert result["user"].id == user.id

            # Should not create duplicate user
            user_count = db_session.query(UserModel).filter_by(email="test@gmail.com").count()
            assert user_count == 1

    @pytest.mark.asyncio
    async def test_authenticate_with_google_existing_email(self, db_session: Session):
        """Test Google OAuth linking to existing user by email"""
        # Create existing user without OAuth
        user = UserModel(
            username="existing_user",
            email="test@gmail.com",
            password_hash="hash",
            is_verified=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        with patch('auth.services.oauth_service.OAuthService.verify_google_token') as mock_verify:
            mock_verify.return_value = MOCK_GOOGLE_USER_DATA

            result, error = await OAuthService.authenticate_with_google(
                db_session,
                MOCK_GOOGLE_TOKEN
            )

            assert error is None
            assert result["user"].id == user.id

            # Verify OAuth connection was created
            oauth_conn = db_session.query(OAuthConnectionModel).filter_by(
                user_id=user.id,
                provider="google"
            ).first()
            assert oauth_conn is not None

    @pytest.mark.asyncio
    async def test_authenticate_with_google_invalid_token(self, db_session: Session):
        """Test Google OAuth with invalid token"""
        with patch('auth.services.oauth_service.OAuthService.verify_google_token') as mock_verify:
            mock_verify.return_value = None

            result, error = await OAuthService.authenticate_with_google(
                db_session,
                "invalid_token"
            )

            assert result is None
            assert error == "Invalid Google token"


@pytest.mark.unit
class TestTelegramOAuth:
    """Test Telegram OAuth functionality"""

    def test_verify_telegram_auth_success(self):
        """Test successful Telegram auth verification"""
        bot_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"

        # Prepare auth data
        auth_data = MOCK_TELEGRAM_DATA.copy()

        # Calculate correct hash
        data_for_hash = {k: v for k, v in auth_data.items() if k != "hash"}
        data_check_arr = [f"{k}={v}" for k, v in sorted(data_for_hash.items())]
        data_check_string = "\n".join(data_check_arr)
        secret_key = hashlib.sha256(bot_token.encode()).digest()
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()

        auth_data["hash"] = calculated_hash

        with patch.dict('os.environ', {'TELEGRAM_BOT_TOKEN': bot_token}):
            result = OAuthService.verify_telegram_auth(auth_data)

        assert result is True

    def test_verify_telegram_auth_invalid_hash(self):
        """Test Telegram auth verification with invalid hash"""
        bot_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
        auth_data = MOCK_TELEGRAM_DATA.copy()
        auth_data["hash"] = "invalid_hash"

        with patch.dict('os.environ', {'TELEGRAM_BOT_TOKEN': bot_token}):
            result = OAuthService.verify_telegram_auth(auth_data)

        assert result is False

    def test_verify_telegram_auth_missing_fields(self):
        """Test Telegram auth verification with missing required fields"""
        bot_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
        auth_data = {"id": "123456789"}  # Missing auth_date and hash

        with patch.dict('os.environ', {'TELEGRAM_BOT_TOKEN': bot_token}):
            result = OAuthService.verify_telegram_auth(auth_data)

        assert result is False

    def test_verify_telegram_auth_no_bot_token(self):
        """Test Telegram auth verification without bot token configured"""
        with patch.dict('os.environ', {}, clear=True):
            result = OAuthService.verify_telegram_auth(MOCK_TELEGRAM_DATA)

        assert result is False

    def test_authenticate_with_telegram_new_user(self, db_session: Session):
        """Test Telegram OAuth authentication with new user"""
        with patch('auth.services.oauth_service.OAuthService.verify_telegram_auth') as mock_verify:
            mock_verify.return_value = True

            result, error = OAuthService.authenticate_with_telegram(
                db_session,
                MOCK_TELEGRAM_DATA
            )

            assert error is None
            assert result is not None
            assert "access_token" in result
            assert "refresh_token" in result
            assert result["token_type"] == "bearer"

            # Verify user was created
            user = result["user"]
            assert user.username == "johndoe"
            assert user.is_verified is True
            assert "@telegram.oauth" in user.email

            # Verify OAuth connection was created
            oauth_conn = db_session.query(OAuthConnectionModel).filter_by(
                provider="telegram",
                provider_user_id="123456789"
            ).first()
            assert oauth_conn is not None
            assert oauth_conn.user_id == user.id

    def test_authenticate_with_telegram_existing_oauth(self, db_session: Session):
        """Test Telegram OAuth authentication with existing OAuth connection"""
        # Create existing user and OAuth connection
        user = UserModel(
            username="existing_tg_user",
            email="123456789@telegram.oauth",
            password_hash="hash",
            is_verified=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        oauth_conn = OAuthConnectionModel(
            user_id=user.id,
            provider="telegram",
            provider_user_id="123456789"
        )
        db_session.add(oauth_conn)
        db_session.commit()

        with patch('auth.services.oauth_service.OAuthService.verify_telegram_auth') as mock_verify:
            mock_verify.return_value = True

            result, error = OAuthService.authenticate_with_telegram(
                db_session,
                MOCK_TELEGRAM_DATA
            )

            assert error is None
            assert result["user"].id == user.id

            # Should not create duplicate user
            user_count = db_session.query(UserModel).filter_by(
                email="123456789@telegram.oauth"
            ).count()
            assert user_count == 1

    def test_authenticate_with_telegram_invalid_auth(self, db_session: Session):
        """Test Telegram OAuth with invalid auth data"""
        with patch('auth.services.oauth_service.OAuthService.verify_telegram_auth') as mock_verify:
            mock_verify.return_value = False

            result, error = OAuthService.authenticate_with_telegram(
                db_session,
                MOCK_TELEGRAM_DATA
            )

            assert result is None
            assert error == "Invalid Telegram authentication data"

    def test_authenticate_with_telegram_unique_username(self, db_session: Session):
        """Test Telegram OAuth creates unique username when conflict exists"""
        # Create existing user with same username
        existing_user = UserModel(
            username="johndoe",
            email="existing@example.com",
            password_hash="hash",
            is_verified=True
        )
        db_session.add(existing_user)
        db_session.commit()

        with patch('auth.services.oauth_service.OAuthService.verify_telegram_auth') as mock_verify:
            mock_verify.return_value = True

            result, error = OAuthService.authenticate_with_telegram(
                db_session,
                MOCK_TELEGRAM_DATA
            )

            assert error is None
            user = result["user"]
            # Username should be made unique (johndoe1, johndoe2, etc.)
            assert user.username.startswith("johndoe")
            assert user.username != "johndoe"


@pytest.mark.unit
class TestOAuthConnectionManagement:
    """Test OAuth connection management functions"""

    def test_find_or_create_oauth_connection_new(self, db_session: Session):
        """Test creating new OAuth connection"""
        # Create user
        user = UserModel(
            username="testuser",
            email="test@example.com",
            password_hash="hash",
            is_verified=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        # Create OAuth connection
        provider_data = {
            "username": "testuser_google",
            "email": "test@gmail.com",
            "picture": "https://example.com/photo.jpg"
        }

        connection = OAuthService.find_or_create_oauth_connection(
            db_session,
            user.id,
            "google",
            "google_123",
            provider_data
        )

        assert connection.user_id == user.id
        assert connection.provider == "google"
        assert connection.provider_user_id == "google_123"
        assert connection.provider_email == "test@gmail.com"
        assert connection.extra_data == provider_data

    def test_find_or_create_oauth_connection_existing(self, db_session: Session):
        """Test updating existing OAuth connection"""
        # Create user and OAuth connection
        user = UserModel(
            username="testuser",
            email="test@example.com",
            password_hash="hash",
            is_verified=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        original_data = {"old": "data"}
        oauth_conn = OAuthConnectionModel(
            user_id=user.id,
            provider="google",
            provider_user_id="google_123",
            extra_data=original_data
        )
        db_session.add(oauth_conn)
        db_session.commit()
        oauth_id = oauth_conn.id

        # Update connection
        new_data = {
            "username": "updated_user",
            "email": "updated@gmail.com",
            "new_field": "new_value"
        }

        connection = OAuthService.find_or_create_oauth_connection(
            db_session,
            user.id,
            "google",
            "google_123",
            new_data
        )

        # Should be same connection (same ID)
        assert connection.id == oauth_id
        assert connection.provider_username == "updated_user"
        assert connection.provider_email == "updated@gmail.com"
        assert connection.extra_data == new_data

        # Should not create duplicate
        count = db_session.query(OAuthConnectionModel).filter_by(
            user_id=user.id,
            provider="google"
        ).count()
        assert count == 1

    def test_get_user_oauth_connections(self, db_session: Session):
        """Test getting all OAuth connections for a user"""
        # Create user
        user = UserModel(
            username="testuser",
            email="test@example.com",
            password_hash="hash",
            is_verified=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        # Create multiple OAuth connections
        google_conn = OAuthConnectionModel(
            user_id=user.id,
            provider="google",
            provider_user_id="google_123"
        )
        telegram_conn = OAuthConnectionModel(
            user_id=user.id,
            provider="telegram",
            provider_user_id="tg_456"
        )
        db_session.add_all([google_conn, telegram_conn])
        db_session.commit()

        # Get connections
        connections = OAuthService.get_user_oauth_connections(db_session, user.id)

        assert len(connections) == 2
        providers = [conn.provider for conn in connections]
        assert "google" in providers
        assert "telegram" in providers

    def test_unlink_oauth_connection_success(self, db_session: Session):
        """Test unlinking OAuth provider from user"""
        # Create user and OAuth connection
        user = UserModel(
            username="testuser",
            email="test@example.com",
            password_hash="hash",
            is_verified=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        oauth_conn = OAuthConnectionModel(
            user_id=user.id,
            provider="google",
            provider_user_id="google_123"
        )
        db_session.add(oauth_conn)
        db_session.commit()

        # Unlink
        success, error = OAuthService.unlink_oauth_connection(
            db_session,
            user.id,
            "google"
        )

        assert success is True
        assert error is None

        # Verify connection was deleted
        remaining = db_session.query(OAuthConnectionModel).filter_by(
            user_id=user.id,
            provider="google"
        ).first()
        assert remaining is None

    def test_unlink_oauth_connection_not_found(self, db_session: Session):
        """Test unlinking non-existent OAuth connection"""
        # Create user without OAuth connection
        user = UserModel(
            username="testuser",
            email="test@example.com",
            password_hash="hash",
            is_verified=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        # Try to unlink
        success, error = OAuthService.unlink_oauth_connection(
            db_session,
            user.id,
            "google"
        )

        assert success is False
        assert error == "No google connection found"


@pytest.mark.integration
class TestOAuthIntegration:
    """Integration tests for OAuth flow"""

    @pytest.mark.asyncio
    async def test_full_google_oauth_flow(self, db_session: Session):
        """Test complete Google OAuth flow"""
        with patch('auth.services.oauth_service.OAuthService.verify_google_token') as mock_verify:
            mock_verify.return_value = MOCK_GOOGLE_USER_DATA

            # First login - creates user
            result1, error1 = await OAuthService.authenticate_with_google(
                db_session,
                MOCK_GOOGLE_TOKEN
            )

            assert error1 is None
            user_id_1 = result1["user"].id
            access_token_1 = result1["access_token"]

            # Second login - returns existing user
            result2, error2 = await OAuthService.authenticate_with_google(
                db_session,
                MOCK_GOOGLE_TOKEN
            )

            assert error2 is None
            user_id_2 = result2["user"].id
            access_token_2 = result2["access_token"]

            # Should be same user
            assert user_id_1 == user_id_2

            # But different tokens (new session)
            assert access_token_1 != access_token_2

            # Verify only one user was created
            user_count = db_session.query(UserModel).filter_by(
                email="test@gmail.com"
            ).count()
            assert user_count == 1

    def test_full_telegram_oauth_flow(self, db_session: Session):
        """Test complete Telegram OAuth flow"""
        with patch('auth.services.oauth_service.OAuthService.verify_telegram_auth') as mock_verify:
            mock_verify.return_value = True

            # First login - creates user
            result1, error1 = OAuthService.authenticate_with_telegram(
                db_session,
                MOCK_TELEGRAM_DATA
            )

            assert error1 is None
            user_id_1 = result1["user"].id

            # Second login - returns existing user
            result2, error2 = OAuthService.authenticate_with_telegram(
                db_session,
                MOCK_TELEGRAM_DATA
            )

            assert error2 is None
            user_id_2 = result2["user"].id

            # Should be same user
            assert user_id_1 == user_id_2

            # Verify only one user was created
            oauth_count = db_session.query(OAuthConnectionModel).filter_by(
                provider="telegram",
                provider_user_id="123456789"
            ).count()
            assert oauth_count == 1

    @pytest.mark.asyncio
    async def test_multiple_oauth_providers_same_user(self, db_session: Session):
        """Test user linking multiple OAuth providers"""
        # Create user with email
        user = UserModel(
            username="testuser",
            email="test@gmail.com",
            password_hash="hash",
            is_verified=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        # Link Google OAuth (matches by email)
        with patch('auth.services.oauth_service.OAuthService.verify_google_token') as mock_verify:
            mock_verify.return_value = MOCK_GOOGLE_USER_DATA

            google_result, google_error = await OAuthService.authenticate_with_google(
                db_session,
                MOCK_GOOGLE_TOKEN
            )

            assert google_error is None
            assert google_result["user"].id == user.id

        # Link Telegram OAuth (manually link to same user)
        with patch('auth.services.oauth_service.OAuthService.verify_telegram_auth') as mock_verify:
            mock_verify.return_value = True

            # Manually create Telegram connection for existing user
            OAuthService.find_or_create_oauth_connection(
                db_session,
                user.id,
                "telegram",
                "123456789",
                MOCK_TELEGRAM_DATA
            )

            telegram_result, telegram_error = OAuthService.authenticate_with_telegram(
                db_session,
                MOCK_TELEGRAM_DATA
            )

            assert telegram_error is None
            assert telegram_result["user"].id == user.id

        # Verify user has both connections
        connections = OAuthService.get_user_oauth_connections(db_session, user.id)
        assert len(connections) == 2
        providers = [conn.provider for conn in connections]
        assert "google" in providers
        assert "telegram" in providers
