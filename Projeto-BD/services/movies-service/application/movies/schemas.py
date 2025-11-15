from pydantic import BaseModel

class MovieIn(BaseModel):
    title: str
    year: int
    genres: list[str] = []
    cast: list[dict] | None = None
    overview: str | None = None
    runtime: int | None = None

class MovieUpdate(BaseModel):
    title: str | None = None
    year: int | None = None
    genres: list[str] = []
    cast: list[dict] | None = None
    overview: str | None = None
    runtime: int | None = None