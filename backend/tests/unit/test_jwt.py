"""
Unit tests for JWT token utilities.

Tests for token generation, verification, and decoding functionality.
Follows TDD cycle: RED -> GREEN -> REFACTOR
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest


class TestAccessTokenGeneration:
    """Tests for access token generation."""

    def test_create_access_token_with_user_id(self):
        """Access token should contain the user ID."""
        from src.utils.jwt import create_access_token, decode_token

        token = create_access_token(user_id=123)

        assert isinstance(token, str)
        assert len(token) > 0

        payload = decode_token(token)
        assert payload.user_id == 123

    def test_create_access_token_with_default_expiration(self):
        """Access token should have default 15-minute expiration."""
        from src.utils.jwt import create_access_token, decode_token

        token = create_access_token(user_id=123)
        payload = decode_token(token)

        # Token should expire in approximately 15 minutes
        now = datetime.now(UTC)
        expected_exp = now + timedelta(minutes=15)

        # Allow 1 minute tolerance for test execution time
        assert abs((payload.exp - expected_exp).total_seconds()) < 60

    def test_create_access_token_with_custom_expiration(self):
        """Access token should accept custom expiration time."""
        from src.utils.jwt import create_access_token, decode_token

        custom_delta = timedelta(hours=1)
        token = create_access_token(user_id=123, expires_delta=custom_delta)
        payload = decode_token(token)

        now = datetime.now(UTC)
        expected_exp = now + custom_delta

        # Allow 1 minute tolerance
        assert abs((payload.exp - expected_exp).total_seconds()) < 60

    def test_create_access_token_with_additional_data(self):
        """Access token should support additional data in payload."""
        from src.utils.jwt import create_access_token, decode_token

        token = create_access_token(
            user_id=123, additional_data={"email": "test@example.com", "role": "user"}
        )
        payload = decode_token(token)

        assert payload.user_id == 123
        assert payload.additional_data.get("email") == "test@example.com"
        assert payload.additional_data.get("role") == "user"


class TestRefreshTokenGeneration:
    """Tests for refresh token generation."""

    def test_create_refresh_token_with_user_id(self):
        """Refresh token should contain the user ID."""
        from src.utils.jwt import create_refresh_token, decode_token

        token = create_refresh_token(user_id=456)

        assert isinstance(token, str)
        assert len(token) > 0

        payload = decode_token(token)
        assert payload.user_id == 456

    def test_create_refresh_token_with_default_expiration(self):
        """Refresh token should have default 7-day expiration."""
        from src.utils.jwt import create_refresh_token, decode_token

        token = create_refresh_token(user_id=456)
        payload = decode_token(token)

        # Token should expire in approximately 7 days
        now = datetime.now(UTC)
        expected_exp = now + timedelta(days=7)

        # Allow 1 minute tolerance
        assert abs((payload.exp - expected_exp).total_seconds()) < 60

    def test_create_refresh_token_with_custom_expiration(self):
        """Refresh token should accept custom expiration time."""
        from src.utils.jwt import create_refresh_token, decode_token

        custom_delta = timedelta(days=14)
        token = create_refresh_token(user_id=456, expires_delta=custom_delta)
        payload = decode_token(token)

        now = datetime.now(UTC)
        expected_exp = now + custom_delta

        # Allow 1 minute tolerance
        assert abs((payload.exp - expected_exp).total_seconds()) < 60


class TestTokenVerification:
    """Tests for token verification."""

    def test_verify_valid_token(self):
        """Valid token should be verified successfully."""
        from src.utils.jwt import create_access_token, verify_token

        token = create_access_token(user_id=789)
        result = verify_token(token)

        assert result is True

    def test_verify_expired_token(self):
        """Expired token should fail verification."""
        from src.utils.jwt import create_access_token, verify_token

        # Create token that expires immediately
        token = create_access_token(user_id=789, expires_delta=timedelta(seconds=-1))
        result = verify_token(token)

        assert result is False

    def test_verify_invalid_token(self):
        """Invalid token should fail verification."""
        from src.utils.jwt import verify_token

        result = verify_token("invalid.token.here")

        assert result is False

    def test_verify_tampered_token(self):
        """Tampered token should fail verification."""
        from src.utils.jwt import create_access_token, verify_token

        token = create_access_token(user_id=789)
        # Tamper with the token by modifying characters
        tampered = token[:-5] + "xxxxx"
        result = verify_token(tampered)

        assert result is False

    def test_verify_token_with_wrong_secret(self):
        """Token verified with wrong secret should fail."""
        from src.utils.jwt import create_access_token

        token = create_access_token(user_id=789)

        # Mock different secret key during verification
        with patch.dict(
            "os.environ",
            {"JWT_SECRET_KEY": "different-secret-key-12345678901234567890"},
        ):
            # Re-import to pick up new secret (in real code, secret is read at runtime)
            import importlib

            from src.utils import jwt

            importlib.reload(jwt)

            # Token should fail verification with different secret
            result = jwt.verify_token(token)
            assert result is False


class TestTokenDecoding:
    """Tests for token decoding."""

    def test_decode_valid_token(self):
        """Valid token should be decoded with correct payload."""
        from src.utils.jwt import create_access_token, decode_token

        token = create_access_token(user_id=999)
        payload = decode_token(token)

        assert payload is not None
        assert payload.user_id == 999
        assert payload.exp is not None

    def test_decode_expired_token_raises_exception(self):
        """Decoding expired token should raise TokenExpiredError."""
        from src.utils.jwt import TokenExpiredError, create_access_token, decode_token

        token = create_access_token(user_id=999, expires_delta=timedelta(seconds=-1))

        with pytest.raises(TokenExpiredError):
            decode_token(token)

    def test_decode_invalid_token_raises_exception(self):
        """Decoding invalid token should raise TokenInvalidError."""
        from src.utils.jwt import TokenInvalidError, decode_token

        with pytest.raises(TokenInvalidError):
            decode_token("not.a.valid.token")

    def test_decode_returns_token_data_model(self):
        """Decoded token should return TokenData model."""
        from src.utils.jwt import TokenData, create_access_token, decode_token

        token = create_access_token(user_id=111)
        payload = decode_token(token)

        assert isinstance(payload, TokenData)
        assert hasattr(payload, "user_id")
        assert hasattr(payload, "exp")


class TestTokenDataModel:
    """Tests for TokenData model."""

    def test_token_data_creation(self):
        """TokenData should be creatable with required fields."""
        from src.utils.jwt import TokenData

        data = TokenData(user_id=123, exp=datetime.now(UTC) + timedelta(hours=1))

        assert data.user_id == 123
        assert data.exp is not None

    def test_token_data_with_additional_data(self):
        """TokenData should support additional data."""
        from src.utils.jwt import TokenData

        data = TokenData(
            user_id=123,
            exp=datetime.now(UTC) + timedelta(hours=1),
            additional_data={"role": "admin"},
        )

        assert data.additional_data["role"] == "admin"
