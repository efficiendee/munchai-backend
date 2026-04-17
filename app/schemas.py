from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=4)


class LoginResponse(BaseModel):
    token: str
    user_id: str


class Recipe(BaseModel):
    id: str
    title: str
    match_score: int
    minutes: int
    difficulty: str
    image_url: str


class HealthResponse(BaseModel):
    status: str
    service: str
