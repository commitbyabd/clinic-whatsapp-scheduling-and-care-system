import bcrypt
from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode(), salt)
    return hashed.decode()
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())



#creating the jwt access token
def create_access_token(user_id: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "role": role,
        # when it was issued, so a password change can end older sessions
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def password_changed_now() -> datetime:
    # A token's iat is in whole seconds, so this is too. A token issued in
    # the same second as the change still works, including the fresh one
    # handed back to whoever changed it.
    return datetime.now(timezone.utc).replace(microsecond=0)


def issued_before(payload: dict, moment: datetime) -> bool:
    """True when the token was issued before `moment` (a password change).
    A token from before iat was added carries none and cannot be judged."""
    issued = payload.get("iat")
    if issued is None:
        return False
    if moment.tzinfo is None:
        # Mongo hands datetimes back without a timezone; they are UTC
        moment = moment.replace(tzinfo=timezone.utc)
    return issued < moment.timestamp()

def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
