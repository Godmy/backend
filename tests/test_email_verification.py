"""
Tests for email verification and password reset flow
"""

import pytest
from auth.services.token_service import token_service
from core.redis_client import redis_client


class TestTokenService:
    """Test token generation and verification"""

    def test_generate_token(self):
        """Test token generation"""
        token = token_service.generate_token()
        assert token is not None
        assert len(token) > 20
        assert isinstance(token, str)

    def test_create_verification_token(self):
        """Test creating verification token"""
        user_id = 123
        token = token_service.create_verification_token(user_id)

        assert token is not None
        assert isinstance(token, str)

        # Verify token exists in Redis
        key = f"{token_service.VERIFICATION_PREFIX}{token}"
        stored_value = redis_client.get(key)
        assert stored_value == str(user_id)

    def test_verify_verification_token(self):
        """Test verifying verification token"""
        user_id = 456
        token = token_service.create_verification_token(user_id)

        # Verify token
        verified_user_id = token_service.verify_verification_token(token)
        assert verified_user_id == user_id

        # Token should be consumed (one-time use)
        verified_again = token_service.verify_verification_token(token)
        assert verified_again is None

    def test_verify_invalid_token(self):
        """Test verifying invalid token"""
        result = token_service.verify_verification_token("invalid-token-123")
        assert result is None

    def test_create_reset_token(self):
        """Test creating password reset token"""
        user_id = 789
        token = token_service.create_reset_token(user_id)

        assert token is not None
        assert isinstance(token, str)

        # Verify token exists in Redis
        key = f"{token_service.RESET_PREFIX}{token}"
        stored_value = redis_client.get(key)
        assert stored_value == str(user_id)

    def test_verify_reset_token(self):
        """Test verifying reset token"""
        user_id = 321
        token = token_service.create_reset_token(user_id)

        # Verify token
        verified_user_id = token_service.verify_reset_token(token)
        assert verified_user_id == user_id

        # Token should be consumed (one-time use)
        verified_again = token_service.verify_reset_token(token)
        assert verified_again is None

    def test_rate_limiting(self):
        """Test rate limiting for email requests"""
        email = "test@example.com"

        # First 3 requests should succeed
        assert token_service.check_rate_limit(email, max_requests=3) is True
        assert token_service.check_rate_limit(email, max_requests=3) is True
        assert token_service.check_rate_limit(email, max_requests=3) is True

        # 4th request should fail
        assert token_service.check_rate_limit(email, max_requests=3) is False

        # Clean up
        redis_client.delete(f"{token_service.RATE_LIMIT_PREFIX}{email}")

    def test_invalidate_all_user_tokens(self):
        """Test invalidating all tokens for a user"""
        user_id = 999

        # Create multiple tokens
        verify_token = token_service.create_verification_token(user_id)
        reset_token = token_service.create_reset_token(user_id)

        # Verify tokens exist
        assert token_service.verify_verification_token(verify_token) == user_id
        assert token_service.verify_reset_token(reset_token) == user_id

        # Invalidate all tokens
        token_service.invalidate_all_user_tokens(user_id)

        # Recreate tokens to test they were deleted
        verify_token_2 = token_service.create_verification_token(user_id)
        reset_token_2 = token_service.create_reset_token(user_id)

        # Original tokens should not work anymore
        assert token_service.verify_verification_token(verify_token) is None
        assert token_service.verify_reset_token(reset_token) is None

        # New tokens should work
        assert token_service.verify_verification_token(verify_token_2) == user_id
        assert token_service.verify_reset_token(reset_token_2) == user_id

    def test_get_token_ttl(self):
        """Test getting TTL for tokens"""
        user_id = 555
        verify_token = token_service.create_verification_token(user_id)

        ttl = token_service.get_verification_token_ttl(verify_token)
        assert ttl > 0
        assert ttl <= token_service.VERIFICATION_TOKEN_TTL

        # Verify token to consume it
        token_service.verify_verification_token(verify_token)

        # TTL should return -2 (not found)
        ttl_after = token_service.get_verification_token_ttl(verify_token)
        assert ttl_after == -2


@pytest.mark.integration
class TestEmailVerificationFlow:
    """Integration tests for complete email verification flow"""

    @pytest.mark.asyncio
    async def test_registration_sends_verification_email(self):
        """Test that registration sends verification email"""
        from core.email_service import email_service
        from auth.services.token_service import token_service

        # Simulate registration
        user_id = 1001
        username = "newuser"
        email = "newuser@example.com"

        # Create verification token
        token = token_service.create_verification_token(user_id)

        # Send verification email
        result = email_service.send_verification_email(
            to_email=email,
            username=username,
            token=token
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_password_reset_sends_email(self):
        """Test that password reset request sends email"""
        from core.email_service import email_service
        from auth.services.token_service import token_service

        # Simulate password reset request
        user_id = 1002
        username = "resetuser"
        email = "resetuser@example.com"

        # Create reset token
        token = token_service.create_reset_token(user_id)

        # Send reset email
        result = email_service.send_password_reset_email(
            to_email=email,
            username=username,
            token=token
        )

        assert result is True

    def test_rate_limit_prevents_spam(self):
        """Test that rate limiting prevents email spam"""
        email = "spam@example.com"

        # First 3 requests succeed
        for i in range(3):
            assert token_service.check_rate_limit(email, max_requests=3) is True

        # 4th request fails
        assert token_service.check_rate_limit(email, max_requests=3) is False

        # Get remaining time
        remaining = token_service.get_rate_limit_remaining(email)
        assert remaining > 0

        # Clean up
        redis_client.delete(f"{token_service.RATE_LIMIT_PREFIX}{email}")


@pytest.mark.unit
class TestRedisClient:
    """Unit tests for Redis client"""

    def test_redis_connection(self):
        """Test Redis connection"""
        assert redis_client.client is not None

    def test_set_and_get(self):
        """Test setting and getting values"""
        key = "test_key"
        value = "test_value"

        result = redis_client.set(key, value, expire_seconds=60)
        assert result is True

        retrieved = redis_client.get(key)
        assert retrieved == value

        # Clean up
        redis_client.delete(key)

    def test_expiration(self):
        """Test key expiration"""
        key = "expiring_key"
        value = "expiring_value"

        redis_client.set(key, value, expire_seconds=2)

        # Should exist initially
        assert redis_client.exists(key) is True

        # Check TTL
        ttl = redis_client.ttl(key)
        assert 0 < ttl <= 2

        # Wait for expiration
        import time
        time.sleep(3)

        # Should not exist after expiration
        assert redis_client.exists(key) is False

    def test_delete(self):
        """Test deleting keys"""
        key = "delete_test"
        redis_client.set(key, "value")

        assert redis_client.exists(key) is True

        result = redis_client.delete(key)
        assert result is True
        assert redis_client.exists(key) is False

    def test_increment(self):
        """Test incrementing counters"""
        key = "counter_test"

        # First increment creates key with value 1
        result = redis_client.incr(key)
        assert result == 1

        # Second increment increases to 2
        result = redis_client.incr(key)
        assert result == 2

        # Increment by custom amount
        result = redis_client.incr(key, amount=5)
        assert result == 7

        # Clean up
        redis_client.delete(key)

    def test_keys_pattern_matching(self):
        """Test finding keys by pattern"""
        # Create multiple keys
        redis_client.set("user:1", "value1")
        redis_client.set("user:2", "value2")
        redis_client.set("other:1", "value3")

        # Find keys matching pattern
        user_keys = redis_client.keys("user:*")
        assert len(user_keys) >= 2
        assert all("user:" in key for key in user_keys)

        # Clean up
        redis_client.delete("user:1")
        redis_client.delete("user:2")
        redis_client.delete("other:1")
