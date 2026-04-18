from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas import RecipeCreateRequest


class RecipeGenerator(ABC):
    @abstractmethod
    def generate_initial_recipes(self, taste_profile: str) -> list[RecipeCreateRequest]:
        raise NotImplementedError


class PlaceholderRecipeGenerator(RecipeGenerator):
    def generate_initial_recipes(self, taste_profile: str) -> list[RecipeCreateRequest]:
        recipes: list[RecipeCreateRequest] = []

        def mk(cat: str, idx: int) -> RecipeCreateRequest:
            return RecipeCreateRequest(
                title=f"{cat} Recipe {idx}",
                description=f"Placeholder {cat.lower()} recipe tailored to taste profile: {taste_profile[:80]}",
                ingredients=["ingredient A", "ingredient B", "ingredient C"],
                steps=["step 1", "step 2", "step 3"],
                minutes=20 + (idx % 5),
                difficulty="Easy",
                image_url="https://example.com/placeholder.png",
                tags=[cat.lower().replace(' ', '-')],
            )

        for i in range(1, 6):
            recipes.append(mk("Breakfast", i))
        for i in range(1, 6):
            recipes.append(mk("Lunch", i))
        for i in range(1, 6):
            recipes.append(mk("Dinner", i))

        return recipes
