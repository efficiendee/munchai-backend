from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.db_mongo import get_db
from app.schemas import LoginRequest, LoginResponse, VerifyAccountRequest
from app.security import (
    get_current_user,
    hash_email,
    issue_bearer_token,
    revoke_current_token,
    verify_password,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest) -> LoginResponse:
    user = get_db().users.find_one(
        {
            "email_hash": hash_email(body.email),
            "is_active": True,
            "verified": True,
        }
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token, ttl = issue_bearer_token(str(user["_id"]))
    return LoginResponse(token=token, user_id=str(user["_id"]), expires_in_seconds=ttl)


@router.post("/verify-account", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def verify_account(body: VerifyAccountRequest) -> Response:
    get_db().users.update_one(
        {"email_hash": hash_email(body.email)},
        {"$set": {"verified": True}},
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def logout(request: Request, _user: dict = Depends(get_current_user)) -> Response:
    revoke_current_token(request)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
