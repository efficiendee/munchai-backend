from __future__ import annotations

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pymongo.errors import DuplicateKeyError

from app.db_mongo import get_db, utc_now
from app.schemas import BootstrapRecipesResponse, UserCreateRequest, UserResponse, UserUpdateRequest
from app.security import get_current_user, hash_email, hash_password
from app.services.email_service import send_verification_email_placeholder
from app.services.recipe_generator import PlaceholderRecipeGenerator

router = APIRouter(prefix="/api/v1/users", tags=["users"])
recipe_generator = PlaceholderRecipeGenerator()


def _to_user_response(doc: dict) -> UserResponse:
    return UserResponse(
        id=str(doc["_id"]),
        username=doc["username"],
        verified=doc.get("verified", False),
        is_active=doc["is_active"],
        taste_profile=doc.get("taste_profile", ""),
        initial_recipes_generated=doc.get("initial_recipes_generated", False),
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )


def _require_owner(path_user_id: str, current_user: dict) -> ObjectId:
    if not ObjectId.is_valid(path_user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    oid = ObjectId(path_user_id)
    if oid != current_user["_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return oid


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(body: UserCreateRequest) -> UserResponse:
    now = utc_now()
    payload = {
        "username": body.username.strip(),
        "email_hash": hash_email(body.email),
        "password_hash": hash_password(body.password),
        "verified": False,
        "is_active": True,
        "taste_profile": body.taste_profile.strip(),
        "initial_recipes_generated": False,
        "created_at": now,
        "updated_at": now,
    }

    try:
        result = get_db().users.insert_one(payload)
    except DuplicateKeyError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")

    created = get_db().users.find_one({"_id": result.inserted_id})
    send_verification_email_placeholder(body.email, str(result.inserted_id))
    return _to_user_response(created)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: str, current_user: dict = Depends(get_current_user)) -> UserResponse:
    oid = _require_owner(user_id, current_user)
    doc = get_db().users.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return _to_user_response(doc)


@router.post("/{user_id}/verify", response_model=UserResponse)
def verify_user(user_id: str, current_user: dict = Depends(get_current_user)) -> UserResponse:
    oid = _require_owner(user_id, current_user)
    result = get_db().users.update_one(
        {"_id": oid},
        {"$set": {"verified": True, "updated_at": utc_now()}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    doc = get_db().users.find_one({"_id": oid})
    return _to_user_response(doc)


@router.post("/{user_id}/bootstrap-recipes", response_model=BootstrapRecipesResponse)
def bootstrap_initial_recipes(user_id: str, current_user: dict = Depends(get_current_user)) -> BootstrapRecipesResponse:
    oid = _require_owner(user_id, current_user)
    user = get_db().users.find_one({"_id": oid})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.get("initial_recipes_generated", False):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Initial recipes already generated")

    generated = recipe_generator.generate_initial_recipes(user.get("taste_profile", ""))
    now = utc_now()
    docs = []
    counts = {"breakfast": 0, "lunch": 0, "dinner": 0}
    for recipe in generated:
        d = recipe.model_dump()
        d["owner_user_id"] = str(oid)
        d["created_at"] = now
        d["updated_at"] = now
        docs.append(d)
        tags = [t.lower() for t in d.get("tags", [])]
        if "breakfast" in tags:
            counts["breakfast"] += 1
        elif "lunch" in tags:
            counts["lunch"] += 1
        elif "dinner" in tags:
            counts["dinner"] += 1

    if docs:
        get_db().recipes.insert_many(docs)
    get_db().users.update_one(
        {"_id": oid},
        {"$set": {"initial_recipes_generated": True, "updated_at": utc_now()}},
    )

    return BootstrapRecipesResponse(count=len(docs), categories=counts)


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str,
    body: UserUpdateRequest,
    current_user: dict = Depends(get_current_user),
) -> UserResponse:
    oid = _require_owner(user_id, current_user)

    updates: dict = {"updated_at": utc_now()}
    if body.username is not None:
        updates["username"] = body.username.strip()
    if body.password is not None:
        updates["password_hash"] = hash_password(body.password)
    if body.is_active is not None:
        updates["is_active"] = body.is_active
    if body.taste_profile is not None:
        updates["taste_profile"] = body.taste_profile.strip()

    result = get_db().users.update_one({"_id": oid}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    doc = get_db().users.find_one({"_id": oid})
    return _to_user_response(doc)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_user(user_id: str, current_user: dict = Depends(get_current_user)) -> Response:
    oid = _require_owner(user_id, current_user)
    result = get_db().users.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
