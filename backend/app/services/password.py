"""Password hashing service (bcrypt)."""

import bcrypt

# bcrypt operates on at most 72 bytes; longer passwords are truncated by the
# algorithm. We hash the raw UTF-8 bytes.
_MAX_BYTES = 72


class PasswordService:
    @staticmethod
    def hash(password: str) -> str:
        pw = password.encode("utf-8")[:_MAX_BYTES]
        return bcrypt.hashpw(pw, bcrypt.gensalt()).decode("utf-8")

    @staticmethod
    def verify(password: str, password_hash: str | None) -> bool:
        if not password_hash:
            return False
        pw = password.encode("utf-8")[:_MAX_BYTES]
        try:
            return bcrypt.checkpw(pw, password_hash.encode("utf-8"))
        except (ValueError, TypeError):
            return False
