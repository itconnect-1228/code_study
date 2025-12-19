"""
Unit tests for password hashing utilities.

Tests for password hashing and verification functionality.
Follows TDD cycle: RED -> GREEN -> REFACTOR
"""


class TestPasswordHashing:
    """Tests for password hashing functionality."""

    def test_hash_password_returns_string(self):
        """hash_password should return a string."""
        from src.utils.security import hash_password

        result = hash_password("test-password")

        assert isinstance(result, str)

    def test_hash_password_returns_non_empty_string(self):
        """hash_password should return a non-empty string."""
        from src.utils.security import hash_password

        result = hash_password("test-password")

        assert len(result) > 0

    def test_hash_password_differs_from_original(self):
        """Hash should be different from the original password."""
        from src.utils.security import hash_password

        password = "my-secret-password"  # noqa: S105
        result = hash_password(password)

        assert result != password

    def test_hash_password_produces_different_hashes_for_same_password(self):
        """Same password should produce different hashes due to salt."""
        from src.utils.security import hash_password

        password = "test-password"  # noqa: S105
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Different hashes due to random salt
        assert hash1 != hash2

    def test_hash_password_starts_with_bcrypt_prefix(self):
        """Hash should start with bcrypt identifier ($2b$)."""
        from src.utils.security import hash_password

        result = hash_password("test-password")

        # bcrypt hashes start with $2a$ or $2b$
        assert result.startswith("$2")

    def test_hash_password_has_consistent_length(self):
        """bcrypt hashes should always be 60 characters."""
        from src.utils.security import hash_password

        # Test with various password lengths
        passwords = ["short", "medium-length-password", "a" * 100]

        for password in passwords:
            result = hash_password(password)
            assert len(result) == 60, f"Hash for '{password}' has wrong length"

    def test_hash_password_handles_empty_string(self):
        """hash_password should handle empty string input."""
        from src.utils.security import hash_password

        result = hash_password("")

        assert isinstance(result, str)
        assert result.startswith("$2")

    def test_hash_password_handles_unicode(self):
        """hash_password should handle unicode characters."""
        from src.utils.security import hash_password

        # Test with Korean characters
        result = hash_password("비밀번호123")

        assert isinstance(result, str)
        assert result.startswith("$2")
        assert len(result) == 60

    def test_hash_password_handles_special_characters(self):
        """hash_password should handle special characters."""
        from src.utils.security import hash_password

        password = 'p@$$w0rd!#%^&*(){}[]|\\:";<>,.?/'  # noqa: S105
        result = hash_password(password)

        assert isinstance(result, str)
        assert result.startswith("$2")

    def test_hash_password_handles_long_password(self):
        """hash_password should handle passwords longer than 72 bytes."""
        from src.utils.security import hash_password

        # Create a password longer than 72 bytes
        long_password = "a" * 100
        result = hash_password(long_password)

        # Should still produce valid hash
        assert isinstance(result, str)
        assert result.startswith("$2")
        assert len(result) == 60


class TestPasswordVerification:
    """Tests for password verification functionality."""

    def test_verify_password_returns_true_for_correct_password(self):
        """verify_password should return True for correct password."""
        from src.utils.security import hash_password, verify_password

        password = "correct-password"  # noqa: S105
        hashed = hash_password(password)

        result = verify_password(password, hashed)

        assert result is True

    def test_verify_password_returns_false_for_wrong_password(self):
        """verify_password should return False for wrong password."""
        from src.utils.security import hash_password, verify_password

        password = "correct-password"  # noqa: S105
        hashed = hash_password(password)

        result = verify_password("wrong-password", hashed)

        assert result is False

    def test_verify_password_is_case_sensitive(self):
        """Password verification should be case-sensitive."""
        from src.utils.security import hash_password, verify_password

        password = "Password123"  # noqa: S105
        hashed = hash_password(password)

        # Different case should fail
        assert verify_password("password123", hashed) is False
        assert verify_password("PASSWORD123", hashed) is False

        # Correct case should pass
        assert verify_password("Password123", hashed) is True

    def test_verify_password_handles_empty_password(self):
        """verify_password should handle empty password."""
        from src.utils.security import hash_password, verify_password

        hashed = hash_password("")

        assert verify_password("", hashed) is True
        assert verify_password("not-empty", hashed) is False

    def test_verify_password_handles_unicode(self):
        """verify_password should handle unicode passwords."""
        from src.utils.security import hash_password, verify_password

        password = "비밀번호123"  # noqa: S105
        hashed = hash_password(password)

        assert verify_password("비밀번호123", hashed) is True
        assert verify_password("다른비밀번호", hashed) is False

    def test_verify_password_handles_special_characters(self):
        """verify_password should handle special characters."""
        from src.utils.security import hash_password, verify_password

        password = "!@#$%^&*()_+-=[]{}|;':\",./<>?"  # noqa: S105
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True
        assert verify_password("different!", hashed) is False

    def test_verify_password_returns_false_for_invalid_hash(self):
        """verify_password should return False for invalid hash format."""
        from src.utils.security import verify_password

        # Invalid hash format
        assert verify_password("password", "invalid-hash") is False
        assert verify_password("password", "") is False
        assert verify_password("password", "not-a-valid-bcrypt-hash") is False

    def test_verify_password_returns_false_for_tampered_hash(self):
        """verify_password should return False for tampered hash."""
        from src.utils.security import hash_password, verify_password

        password = "test-password"  # noqa: S105
        hashed = hash_password(password)

        # Tamper with the hash
        tampered = hashed[:-5] + "xxxxx"

        assert verify_password(password, tampered) is False

    def test_verify_password_works_with_multiple_hashes(self):
        """Each password should only match its own hash."""
        from src.utils.security import hash_password, verify_password

        password1 = "password-one"
        password2 = "password-two"
        hash1 = hash_password(password1)
        hash2 = hash_password(password2)

        # Each password should only verify against its own hash
        assert verify_password(password1, hash1) is True
        assert verify_password(password1, hash2) is False
        assert verify_password(password2, hash1) is False
        assert verify_password(password2, hash2) is True

    def test_verify_password_handles_long_password(self):
        """verify_password should handle passwords longer than 72 bytes."""
        from src.utils.security import hash_password, verify_password

        long_password = "a" * 100
        hashed = hash_password(long_password)

        # Should verify correctly (both hash and verify truncate to 72 bytes)
        assert verify_password(long_password, hashed) is True

        # Password with same first 72 characters should also match
        # (because bcrypt truncates to 72 bytes)
        same_prefix = "a" * 72 + "b" * 28
        assert verify_password(same_prefix, hashed) is True


class TestSecurityProperties:
    """Tests for security properties of the implementation."""

    def test_hashing_takes_non_trivial_time(self):
        """Hashing should take some time (resistant to brute-force)."""
        import time

        from src.utils.security import hash_password

        start = time.time()
        hash_password("test-password")
        elapsed = time.time() - start

        # Should take at least 10ms (bcrypt is intentionally slow)
        assert elapsed >= 0.01, f"Hashing was too fast: {elapsed}s"

    def test_different_passwords_produce_different_hashes(self):
        """Different passwords should produce different hashes."""
        from src.utils.security import hash_password

        passwords = ["password1", "password2", "password3"]
        hashes = [hash_password(p) for p in passwords]

        # All hashes should be unique
        assert len(set(hashes)) == len(passwords)

    def test_hash_contains_cost_factor(self):
        """Hash should contain the cost factor."""
        from src.utils.security import hash_password

        result = hash_password("test-password")

        # bcrypt hash format: $2b$XX$ where XX is the cost factor
        # Default cost factor is 12
        parts = result.split("$")
        assert len(parts) >= 4
        # Cost factor is in parts[2]
        cost = int(parts[2])
        assert 4 <= cost <= 31  # Valid bcrypt cost range
