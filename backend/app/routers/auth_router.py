from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..auth import issue_jwt, verify_google_id_token
from ..config import settings
from ..db import get_db
from ..models import User
from ..schemas import LoginRequest, LoginResponse, ScopeOut, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


def _login_response(user: User) -> LoginResponse:
    token = issue_jwt(user)
    return LoginResponse(
        access_token=token,
        user=UserOut(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role,
            scopes=[ScopeOut(store_id=s.store_id, store_type=s.store_type) for s in user.scopes],
        ),
    )


@router.get("/dev-login", response_model=LoginResponse)
def dev_login(email: str = Query(...), db: Session = Depends(get_db)):
    """Local-dev-only shortcut that skips real Google OAuth. Requires the explicit
    ALLOW_DEV_LOGIN=true env var, independent of db_backend, so it can be used
    during build/test against Snowflake too — must be unset before real deployment."""
    if not settings.allow_dev_login:
        raise HTTPException(status_code=404, detail="Not found")
    user = db.query(User).filter(User.email == email, User.is_active == True).first()  # noqa: E712
    if not user:
        raise HTTPException(status_code=403, detail="No such user")
    return _login_response(user)


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    claims = verify_google_id_token(payload.id_token)
    email = claims["email"]

    user = db.query(User).filter(User.email == email, User.is_active == True).first()  # noqa: E712
    if not user:
        raise HTTPException(status_code=403, detail="This Google account is not provisioned for the app")

    return _login_response(user)
