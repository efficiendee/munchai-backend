from __future__ import annotations

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.db_mongo import get_db, utc_now
from app.schemas import RecipeCreateRequest, RecipeResponse, RecipeUpdateRequest
from app.security import get_current_user

router = APIRouter(prefix="/api/v1/recipes", tags=["recipes"])


def _to_recipe_response(doc: dict) -> RecipeResponse:
    return RecipeResponse(
        id=str(doc["_id"]),
        title=doc["title"],
        description=doc["description"],
        ingredients=doc["ingredients"],
        steps=doc["steps"],
        minutes=doc["minutes"],
        difficulty=doc["difficulty"],
        image_url=doc["image_url"],
        tags=doc.get("tags", []),
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )


def _recipe_for_owner(recipe_id: str, owner_user_id: str) -> dict | None:
    if not ObjectId.is_valid(recipe_id):
        return None
    return get_db().recipes.find_one({"_id": ObjectId(recipe_id), "owner_user_id": owner_user_id})


@router.post("", response_model=RecipeResponse, status_code=status.HTTP_201_CREATED)
def create_recipe(body: RecipeCreateRequest, current_user: dict = Depends(get_current_user)) -> RecipeResponse:
    now = utc_now()
    payload = body.model_dump()
    payload["owner_user_id"] = str(current_user["_id"])
    payload["created_at"] = now
    payload["updated_at"] = now

    result = get_db().recipes.insert_one(payload)
    created = get_db().recipes.find_one({"_id": result.inserted_id})
    return _to_recipe_response(created)


@router.get("", response_model=list[RecipeResponse])
def list_recipes(current_user: dict = Depends(get_current_user)) -> list[RecipeResponse]:
    docs = list(get_db().recipes.find({"owner_user_id": str(current_user["_id"])}).sort("created_at", -1))
    return [_to_recipe_response(doc) for doc in docs]


@router.get("/{recipe_id}", response_model=RecipeResponse)
def get_recipe(recipe_id: str, current_user: dict = Depends(get_current_user)) -> RecipeResponse:
    doc = _recipe_for_owner(recipe_id, str(current_user["_id"]))
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")
    return _to_recipe_response(doc)


@router.put("/{recipe_id}", response_model=RecipeResponse)
def replace_recipe(
    recipe_id: str,
    body: RecipeCreateRequest,
    current_user: dict = Depends(get_current_user),
) -> RecipeResponse:
    existing = _recipe_for_owner(recipe_id, str(current_user["_id"]))
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")

    payload = body.model_dump()
    payload["owner_user_id"] = str(current_user["_id"])
    payload["created_at"] = existing["created_at"]
    payload["updated_at"] = utc_now()

    get_db().recipes.replace_one({"_id": existing["_id"]}, payload)
    doc = get_db().recipes.find_one({"_id": existing["_id"]})
    return _to_recipe_response(doc)


@router.patch("/{recipe_id}", response_model=RecipeResponse)
def update_recipe(
    recipe_id: str,
    body: RecipeUpdateRequest,
    current_user: dict = Depends(get_current_user),
) -> RecipeResponse:
    existing = _recipe_for_owner(recipe_id, str(current_user["_id"]))
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")

    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    updates["updated_at"] = utc_now()

    get_db().recipes.update_one({"_id": existing["_id"]}, {"$set": updates})
    doc = get_db().recipes.find_one({"_id": existing["_id"]})
    return _to_recipe_response(doc)


@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_recipe(recipe_id: str, current_user: dict = Depends(get_current_user)) -> Response:
    existing = _recipe_for_owner(recipe_id, str(current_user["_id"]))
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")

    get_db().recipes.delete_one({"_id": existing["_id"]})
    return Response(status_code=status.HTTP_204_NO_CONTENT)
