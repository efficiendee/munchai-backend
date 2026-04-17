from fastapi import APIRouter, Depends

from app.schemas import Recipe
from app.security import check_api_key, check_rate_limit

router = APIRouter(prefix="/api/v1/recipes", tags=["recipes"])

DUMMY_RECIPES = [
    Recipe(
        id="1",
        title="Soy-Garlic Chicken Rice Bowl",
        match_score=95,
        minutes=20,
        difficulty="Easy",
        image_url="assets/images/recipe1.png",
    ),
    Recipe(
        id="2",
        title="Salmon Poke Bowl",
        match_score=88,
        minutes=18,
        difficulty="Easy",
        image_url="assets/images/recipe2.png",
    ),
]


@router.get("")
async def list_recipes(
    _api: None = Depends(check_api_key),
    _rate: None = Depends(check_rate_limit),
) -> list[Recipe]:
    return DUMMY_RECIPES
