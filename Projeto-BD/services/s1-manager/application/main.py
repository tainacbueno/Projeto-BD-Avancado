from fastapi import FastAPI, HTTPException, Query
from sqlalchemy.orm import Session
from .models import Base, S1Log
from .db import engine, SessionLocal
from .seed import fake_user, fake_movie, fake_review, fake_rating
from .clients import (
    create_user, create_movie, create_review, create_rating
)
import requests
import os

api = FastAPI(title="s1-manager")

@api.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@api.post("/run")
async def run_scenario(
    users: int = Query(5, ge=0),
    movies: int = Query(5, ge=0),
    ratings: int = Query(10, ge=0),
    reviews: int = Query(10, ge=0)
):
    """
    Gera dados e chama S2:
      - cria <users> usuários (users-service)
      - cria <movies> filmes (movies-service /movies)
      - cria <ratings> notas (ratings-service /ratings)
      - cria <reviews> resenhas (movies-service /reviews)
    Todas as requests/responses são logadas em s1_logs (Postgres).
    """

    db_ctx = get_db()
    db: Session = next(db_ctx)

    user_ids, movie_ids = [], []

    # 1) Usuários
    for _ in range(users):
        resp = await create_user(db, fake_user())
        if not resp or resp.status_code >= 400:
            continue
        try:
            data = resp.json()
            user_ids.append(data["id"])
        except Exception:
            continue

    # 2) Filmes
    for _ in range(movies):
        resp = await create_movie(db, fake_movie())
        if not resp or resp.status_code >= 400:
            continue
        try:
            data = resp.json()
            movie_ids.append(data["id"])
        except Exception:
            continue

    if not user_ids or not movie_ids:
        # encerra a sessão antes de retornar
        try:
            next(db_ctx)
        except StopIteration:
            pass
        return {
            "ok": False,
            "users_created": len(user_ids),
            "movies_created": len(movie_ids),
            "ratings_created": 0,
            "reviews_created": 0,
            "message": "Nenhum usuário ou filme válido foi criado. "
                    "Verifique se os S2 estão acessíveis e se os IDs retornados estão sendo extraídos corretamente."
        }

    total_users = len(user_ids)
    total_movies = len(movie_ids)

    # Ratings (Redis)
    for i in range(ratings):
        payload = fake_rating(user_ids[i % total_users], movie_ids[i % total_movies])
        await create_rating(db, payload)

    # Reviews (Mongo)
    for i in range(reviews):
        payload = fake_review(user_ids[i % total_users], movie_ids[i % total_movies])
        await create_review(db, payload)

    try:
        next(db_ctx)
    except StopIteration:
        pass

    return {
        "ok": True,
        "users_created": len(user_ids),
        "movies_created": len(movie_ids),
        "ratings_created": ratings,
        "reviews_created": reviews
    }

@api.get("/logs")
def logs(limit: int = 50):
    with next(get_db()) as db:
        rows = db.query(S1Log).order_by(S1Log.id.desc()).limit(limit).all()
        return [
            {
                "id": l.id, "ts": str(l.ts), "service": l.service,
                "method": l.method, "url": l.url,
                "status": l.response_status
            } for l in rows
        ]
    
# DELETA OS DADOS DE TODOS OS BANCOS
@api.delete("/reset", status_code=200)
def reset_all():
    """
    Limpa TODOS os serviços usando chamadas HTTP.
    """
    result = {
        "users_deleted": 0,
        "movies_deleted": False,
        "reviews_deleted": False,
        "ratings_deleted": False,
        "errors": []
    }
    
    MOVIES_URL  = os.getenv("MOVIES_URL", "http://movies-service:8000")
    USERS = os.getenv("USERS_URL", "http://users-service:8000")
    MOVIES = MOVIES_URL + "/movies"
    REVIEWS = MOVIES_URL + "/reviews"
    RATINGS = os.getenv("RATINGS_URL", "http://ratings-service:8000")

    # ----------------------
    # 1) USERS-SERVICE
    # ----------------------
    try:
        r = requests.get(f"{USERS}/users?limit=100000", timeout=5)
        if r.status_code == 200:
            users = r.json()
            deleted = 0
            for u in users:
                uid = u.get("id")
                if uid:
                    dr = requests.delete(f"{USERS}/users/{uid}", timeout=5)
                    if dr.status_code in (200, 204):
                        deleted += 1
            result["users_deleted"] = deleted
        else:
            result["errors"].append("GET /users failed")
    except Exception as e:
        result["errors"].append(f"users-service error: {e}")

    # ----------------------
    # 2) MOVIES-SERVICE
    # ----------------------
    try:
        r = requests.delete(f"{MOVIES}/all", timeout=5)
        if r.status_code == 200:
            result["movies_deleted"] = True
        else:
            result["errors"].append("DELETE /movies/all failed")
    except Exception as e:
        result["errors"].append(f"movies-service movies error: {e}")

    # REVIEWS
    try:
        r = requests.delete(f"{REVIEWS}/all", timeout=5)
        if r.status_code == 200:
            result["reviews_deleted"] = True
        else:
            result["errors"].append("DELETE /reviews/all failed")
    except Exception as e:
        result["errors"].append(f"movies-service reviews error: {e}")

    # ----------------------
    # 3) RATINGS-SERVICE
    # ----------------------
    try:
        r = requests.delete(f"{RATINGS}/ratings/all", timeout=5)
        if r.status_code == 200:
            result["ratings_deleted"] = True
        else:
            result["errors"].append("DELETE /ratings/all failed")
    except Exception as e:
        result["errors"].append(f"ratings-service error: {e}")

    return {"ok": True, "result": result}