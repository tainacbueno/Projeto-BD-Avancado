from fastapi import FastAPI
from .db import ensure_indexes
from .movies.routes import router as movies_router
from .reviews.routes import router as reviews_router

api = FastAPI(title="movies-service")

@api.on_event("startup")
def startup():
    ensure_indexes()

api.include_router(movies_router, prefix="/movies", tags=["movies"])
api.include_router(reviews_router, prefix="/reviews", tags=["reviews"])