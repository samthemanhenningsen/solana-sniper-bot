"""Authentication — stdlib-only password hashing (scrypt) and HMAC-signed session cookies."""

from __future__ import annotations

import hashlib
import hmac
import secrets
import time

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from .db import get_db
from .models import User
from .settings import settings

SESSION_COOKIE = "gp_session"
SESSION_TTL = 60 * 60 * 24 * 14  # 14 days


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, digest_hex = stored.split("$", 1)
        digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt_hex), n=2**14, r=8, p=1)
        return hmac.compare_digest(digest.hex(), digest_hex)
    except (ValueError, TypeError):
        return False


def _sign(payload: str) -> str:
    return hmac.new(settings.secret_key.encode(), payload.encode(), hashlib.sha256).hexdigest()


def make_session_token(user_id: int) -> str:
    payload = f"{user_id}.{int(time.time()) + SESSION_TTL}"
    return f"{payload}.{_sign(payload)}"


def parse_session_token(token: str) -> int | None:
    try:
        user_id, expiry, sig = token.rsplit(".", 2)
        payload = f"{user_id}.{expiry}"
        if not hmac.compare_digest(sig, _sign(payload)):
            return None
        if int(expiry) < time.time():
            return None
        return int(user_id)
    except (ValueError, TypeError):
        return None


def current_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    user_id = parse_session_token(token)
    if user_id is None:
        return None
    return db.get(User, user_id)
