import os, json, httpx
from sqlalchemy.orm import Session
from .models import S1Log

USERS_URL   = os.getenv("USERS_URL", "http://users-service:8000")
MOVIES_URL  = os.getenv("MOVIES_URL", "http://movies-service:8000")
RATINGS_URL = os.getenv("RATINGS_URL", "http://ratings-service:8000")

DEFAULT_TIMEOUT = httpx.Timeout(10.0)

async def call_and_log(db: Session, service: str, method: str, url: str, json_body: dict | None):
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        try:
            resp = await client.request(method, url, json=json_body)
            status = resp.status_code
            text = resp.text
        except Exception as e:
            status = 599
            text = f"client_error: {type(e).__name__}: {e}"

    log = S1Log(
        service=service,
        method=method,
        url=url,
        request_body=json.dumps(json_body or {}),
        response_status=status,
        response_body=text,
    )
    db.add(log)
    db.commit()
    return resp if isinstance(text, str) and status != 599 else None

# Users
async def create_user(db: Session, payload: dict):
    return await call_and_log(db, "users-service", "POST", f"{USERS_URL}/users", payload)

# Movies
async def create_movie(db: Session, payload: dict):
    return await call_and_log(db, "movies-service", "POST", f"{MOVIES_URL}/movies/", payload)

# Reviews
async def create_review(db: Session, payload: dict):
    return await call_and_log(db, "movies-service", "POST", f"{MOVIES_URL}/reviews/", payload)

# Ratings
async def create_rating(db: Session, payload: dict):
    return await call_and_log(db, "ratings-service", "POST", f"{RATINGS_URL}/ratings", payload)