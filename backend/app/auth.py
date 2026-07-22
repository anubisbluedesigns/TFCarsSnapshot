import datetime

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from .config import settings
from .models import Role, User

bearer_scheme = HTTPBearer()


def verify_google_id_token(id_token_str: str) -> dict:
    """Verify a Google GSI id_token and return its claims (email, name, sub)."""
    from google.oauth2 import id_token as google_id_token
    from google.auth.transport import requests as google_requests

    claims = google_id_token.verify_oauth2_token(
        id_token_str, google_requests.Request(), settings.google_client_id
    )
    return claims


def issue_jwt(user: User) -> str:
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        # each scope: {"store_id": int, "store_type": "new"|"used"|None (=both)}
        "scopes": [{"store_id": s.store_id, "store_type": s.store_type} for s in user.scopes],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=settings.jwt_expires_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_jwt(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


class CurrentUser:
    def __init__(self, id: int, email: str, role: str, scopes: list[dict]):
        self.id = id
        self.email = email
        self.role = role
        self.scopes = scopes  # [{"store_id": int, "store_type": str|None}]

    @property
    def store_ids(self) -> list[int]:
        return sorted({s["store_id"] for s in self.scopes})

    def _scope_matches(self, store_id: int, store_type: str | None) -> bool:
        for s in self.scopes:
            if s["store_id"] != store_id:
                continue
            if s["store_type"] is None or store_type is None or s["store_type"] == store_type:
                return True
        return False

    def can_edit_store(self, store_id: int, store_type: str | None = None) -> bool:
        """Full field edit — only the full_edit role, only within their scoped (store, type)."""
        if self.role != Role.full_edit.value:
            return False
        return self._scope_matches(store_id, store_type)

    def can_edit_status(self, store_id: int, store_type: str | None = None) -> bool:
        """Status-only edit — full_edit (within scope) or manager (anywhere they can view)."""
        if self.role == Role.full_edit.value:
            return self._scope_matches(store_id, store_type)
        if self.role == Role.manager.value:
            return self._scope_matches(store_id, store_type)
        return False

    def can_toggle_reserved(self, store_id: int, store_type: str | None = None) -> bool:
        if self.role in (Role.full_edit.value, Role.manager.value):
            return self._scope_matches(store_id, store_type)
        if self.role == Role.sales_rep.value:
            return self._scope_matches(store_id, store_type)
        return False

    def can_view_store(self, store_id: int, store_type: str | None = None) -> bool:
        return self._scope_matches(store_id, store_type)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> CurrentUser:
    claims = decode_jwt(credentials.credentials)
    return CurrentUser(
        id=int(claims["sub"]),
        email=claims["email"],
        role=claims["role"],
        scopes=claims.get("scopes", []),
    )


def require_any_role(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    return user
