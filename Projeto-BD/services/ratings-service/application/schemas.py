from pydantic import BaseModel, Field

class RatingIn(BaseModel):
    movie_id: str = Field(..., min_length=1)
    user_id: str  = Field(..., min_length=1)
    score: int    = Field(..., ge=1, le=5)
    comment: str | None = None

class RatingUpdate(BaseModel):
    score: int | None = Field(None, ge=1, le=5)
    comment: str | None = None
