from __future__ import annotations

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pymongo.errors import DuplicateKeyError

from app.db_mongo import get_db, utc_now
from app.schemas import UserCreateRequest, UserResponse, UserUpdateRequest
from app.security import check_api_key, check_rate_limit, hash_email, hash_password

router = APIRouter(prefix="/api/v1/users", tags=["users"])


def _to_user_response(doc: dict) -> UserResponse:
    return UserResponse(
        id=str(doc["_id"]),
        username=doc["username"],
        verified=doc.get("verified", False),
        is_active=doc["is_active"],
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    body: UserCreateRequest,
    _api: None = Depends(check_api_key),
    _rate: None = Depends(check_rate_limit),
) -> UserResponse:
    now = utc_now()
    payload = {
        "username": body.username.strip(),
        "email_hash": hash_email(body.email),
        "password_hash": hash_password(body.password),
        "verified": False,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }

    try:
        result = get_db().users.insert_one(payload)
    except DuplicateKeyError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")

    created = get_db().users.find_one({"_id": result.inserted_id})
    return _to_user_response(created)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: str,
    _api: None = Depends(check_api_key),
    _rate: None = Depends(check_rate_limit),
) -> UserResponse:
    doc = get_db().users.find_one({"_id": ObjectId(user_id)}) if ObjectId.is_valid(user_id) else None
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return _to_user_response(doc)


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str,
    body: UserUpdateRequest,
    _api: None = Depends(check_api_key),
    _rate: None = Depends(check_rate_limit),
) -> UserResponse:
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    updates: dict = {"updated_at": utc_now()}
    if body.username is not None:
        updates["username"] = body.username.strip()
    if body.password is not None:
        updates["password_hash"] = hash_password(body.password)
    if body.is_active is not None:
        updates["is_active"] = body.is_active

    result = get_db().users.update_one({"_id": ObjectId(user_id)}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    doc = get_db().users.find_one({"_id": ObjectId(user_id)})
    return _to_user_response(doc)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_user(
    user_id: str,
    _api: None = Depends(check_api_key),
    _rate: None = Depends(check_rate_limit),
) -> Response:
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    result = get_db().users.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
