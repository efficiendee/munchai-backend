from fastapi import APIRouter, Depends, HTTPException, status

from app.db_mongo import get_db
from app.schemas import LoginRequest, LoginResponse
from app.security import check_api_key, check_rate_limit, hash_email, verify_password

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(
    body: LoginRequest,
    _api: None = Depends(check_api_key),
    _rate: None = Depends(check_rate_limit),
) -> LoginResponse:
    user = get_db().users.find_one({
        "email_hash": hash_email(body.email),
        "is_active": True,
        "verified": True,
    })
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    return LoginResponse(token="dummy-session-token", user_id=str(user["_id"]))
