from fastapi import APIRouter, Depends

from app.schemas import LoginRequest, LoginResponse
from app.security import check_api_key, check_rate_limit

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    _api: None = Depends(check_api_key),
    _rate: None = Depends(check_rate_limit),
) -> LoginResponse:
    user_id = body.email.split("@")[0] if "@" in body.email else "demo-user"
    return LoginResponse(token="dummy-session-token", user_id=user_id)
