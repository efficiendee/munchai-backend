from pydantic import BaseModel, EmailStr, Field


class HealthResponse(BaseModel):
    status: str
    service: str


class UserCreateRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserUpdateRequest(BaseModel):
    username: str | None = Field(default=None, min_length=3, max_length=50)
    password: str | None = Field(default=None, min_length=8, max_length=128)
    is_active: bool | None = None


class UserResponse(BaseModel):
    id: str
    username: str
    verified: bool
    is_active: bool
    created_at: str
    updated_at: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginResponse(BaseModel):
    token: str
    user_id: str


class RecipeBase(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    description: str = Field(min_length=2, max_length=2000)
    ingredients: list[str]
    steps: list[str]
    minutes: int = Field(ge=1, le=600)
    difficulty: str = Field(min_length=2, max_length=32)
    image_url: str = Field(min_length=1, max_length=2000)
    tags: list[str] = []


class RecipeCreateRequest(RecipeBase):
    pass


class RecipeUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = Field(default=None, min_length=2, max_length=2000)
    ingredients: list[str] | None = None
    steps: list[str] | None = None
    minutes: int | None = Field(default=None, ge=1, le=600)
    difficulty: str | None = Field(default=None, min_length=2, max_length=32)
    image_url: str | None = Field(default=None, min_length=1, max_length=2000)
    tags: list[str] | None = None


class RecipeResponse(RecipeBase):
    id: str
    created_at: str
    updated_at: str
