from fastapi import FastAPI, APIRouter, HTTPException
from pydantic import BaseModel, Field
from redis import Redis
import os, time, requests
from .schemas import RatingIn, RatingUpdate

api = FastAPI(title="ratings-service")
router = APIRouter()

redis = Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    db=int(os.getenv("REDIS_DB", "0")),
    decode_responses=True, 
)

def rating_key(movie_id: str, user_id: str) -> str:
    return f"rating:movie:{movie_id}:user:{user_id}"

def fetch_movie_name(movie_id: str) -> str | None:
    try:
        req = requests.get(f"http://movies-service:8000/movies/{movie_id}", timeout=2)
        if req.status_code == 200:
            data = req.json()
            return data.get("title")
    except Exception as err:
        print("Erro ao consultar movies-service:", err)
    return None


@router.post("/ratings", status_code=201)
def rate(payload: RatingIn):
    key = rating_key(payload.movie_id, payload.user_id)

    # Lê rating anterior se existir
    prev_score_str = redis.hget(key, "score")
    prev_score = int(prev_score_str) if prev_score_str is not None else None

    # Salva/atualiza rating no hash
    now_ts = int(time.time())
    redis.hset(
        key,
        mapping={
            "score": int(payload.score),
            "comment": (payload.comment or ""),
            "time_stamp": now_ts,
        },
    )

    # Chaves de agregados do filme
    ckey = f"movie:{payload.movie_id}:rating_count"
    skey = f"movie:{payload.movie_id}:rating_sum"

    pipe = redis.pipeline()
    if prev_score is None:
        # Novo rating: incrementa count e soma
        pipe.incr(ckey)
        pipe.incrby(skey, int(payload.score))
    else:
        delta = int(payload.score) - prev_score
        if delta != 0:
            pipe.incrby(skey, delta)

    pipe.get(ckey)
    pipe.get(skey)
    res = pipe.execute()

    if prev_score is None:
        # res = [new_count, new_sum, count_str, sum_str]
        count_str, sum_str = res[-2], res[-1]
    else:
        # res = [maybe_new_sum, count_str, sum_str]  (quando delta=0, o primeiro é None)
        count_str, sum_str = res[-2], res[-1]

    try:
        count = int(count_str or 0)
        sum_  = int(sum_str or 0)
    except ValueError:
        raise HTTPException(status_code=500, detail="Agregados inválidos no Redis.")

    avg = (sum_ / count) if count > 0 else 0.0

    # Atualiza leaderboard por média
    redis.zadd("top:avg_ratings", {payload.movie_id: float(avg)})

    movie_name = fetch_movie_name(payload.movie_id)

    return {
        "movie_name": movie_name,
        **payload.dict()
    }

@router.get("/ratings/{movie_id}/{user_id}")
def get_user_rating(movie_id: str, user_id: str):
    key = rating_key(movie_id, user_id)
    data = redis.hgetall(key)

    if not data:
        raise HTTPException(status_code=404, detail="Rating não encontrado.")

    return {
        "movie_id": movie_id,
        "user_id": user_id,
        "score": int(data.get("score", 0)),
        "comment": data.get("comment", ""),
    }

@router.get("/ratings/{movie_id}")
def get_movie_ratings(movie_id: str):    
    movie_name = fetch_movie_name(movie_id)

    if movie_name is None:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    ckey = f"movie:{movie_id}:rating_count"
    skey = f"movie:{movie_id}:rating_sum"

    count_str = redis.get(ckey)
    sum_str   = redis.get(skey)

    count = int(count_str or 0)
    sum_  = int(sum_str or 0)

    avg = (sum_ / count) if count > 0 else 0.0

    return {
        "movie_name": movie_name,
        "movie_id": movie_id,
        "count": count,
        "sum": sum_,
        "average": avg,
    }

@router.put("/ratings/{movie_id}/{user_id}")
def update_rating(movie_id: str, user_id: str, payload: RatingUpdate):
    key = rating_key(movie_id, user_id)

    # Pega rating anterior
    prev_data = redis.hgetall(key)
    if not prev_data:
        raise HTTPException(status_code=404, detail="Rating não encontrado.")

    prev_score = int(prev_data.get("score", 0))

    # Score novo (mantém o anterior se não enviado)
    new_score = payload.score if payload.score is not None else prev_score

    # Salva o rating atualizado
    now_ts = int(time.time())
    redis.hset(
        key,
        mapping={
            "score": new_score,
            "comment": payload.comment if payload.comment is not None else prev_data.get("comment", ""),
            "ts": now_ts,
        },
    )

    # Atualização de agregados
    ckey = f"movie:{movie_id}:rating_count"
    skey = f"movie:{movie_id}:rating_sum"

    delta = new_score - prev_score

    pipe = redis.pipeline()
    if delta != 0:
        pipe.incrby(skey, delta)

    pipe.get(ckey)
    pipe.get(skey)
    res = pipe.execute()

    count_str, sum_str = res[-2], res[-1]

    count = int(count_str or 0)
    sum_ = int(sum_str or 0)

    avg = (sum_ / count) if count > 0 else 0.0

    # Atualiza leaderboard
    redis.zadd("top:avg_ratings", {movie_id: float(avg)})

    movie_name = fetch_movie_name(movie_id)

    return {
        "movie_name": movie_name,
        "movie_id": movie_id,
        "user_id": user_id,
        "score": new_score,
        "comment": payload.comment if payload.comment is not None else prev_data.get("comment", ""),
        "average": avg,
        "count": count,
    }

# DELETA UM RATING DE UM USUÁRIO PARA UM FILME
@router.delete("/ratings/{movie_id}/{user_id}", status_code=200)
def delete_rating(movie_id: str, user_id: str):
    key = rating_key(movie_id, user_id)

    # Busca rating existente
    data = redis.hgetall(key)
    if not data:
        raise HTTPException(status_code=404, detail="Rating não encontrado.")

    try:
        prev_score = int(data.get("score", 0))
    except ValueError:
        prev_score = 0

    # Remove o rating
    redis.delete(key)

    # Atualiza agregados
    ckey = f"movie:{movie_id}:rating_count"
    skey = f"movie:{movie_id}:rating_sum"

    pipe = redis.pipeline()
    pipe.decr(ckey)
    pipe.decrby(skey, prev_score)
    pipe.get(ckey)
    pipe.get(skey)
    res = pipe.execute()

    new_count_str, new_sum_str = res[-2], res[-1]
    new_count = int(new_count_str or 0)
    new_sum   = int(new_sum_str or 0)

    # Recalcula média
    new_avg = (new_sum / new_count) if new_count > 0 else 0.0

    # Atualiza leaderboard
    redis.zadd("top:avg_ratings", {movie_id: float(new_avg)})

    movie_name = fetch_movie_name(movie_id)

    return {
        "message": "Rating removido com sucesso.",
        "movie_id": movie_id,
        "movie_name": movie_name,
        "user_id": user_id,
        "new_count": new_count,
        "new_sum": new_sum,
        "new_average": new_avg,
    }

# DELETA TODOS OS RATINGS DE UM FILME
@router.delete("/ratings/movie/{movie_id}", status_code=200)
def delete_all_ratings_for_movie(movie_id: str):
    pattern = f"rating:movie:{movie_id}:user:*"
    keys = redis.keys(pattern)

    deleted = 0
    total_removed_score = 0

    for key in keys:
        data = redis.hgetall(key)
        if data:
            try:
                total_removed_score += int(data.get("score", 0))
            except ValueError:
                pass
        redis.delete(key)
        deleted += 1

    # zera agregados
    ckey = f"movie:{movie_id}:rating_count"
    skey = f"movie:{movie_id}:rating_sum"
    redis.set(ckey, 0)
    redis.set(skey, 0)

    # média agora é 0
    redis.zadd("top:avg_ratings", {movie_id: 0.0})

    movie_name = fetch_movie_name(movie_id)

    return {
        "message": "Todos os ratings deste filme foram removidos.",
        "movie_id": movie_id,
        "movie_name": movie_name,
        "removed_ratings": deleted,
        "removed_score_sum": total_removed_score,
        "new_count": 0,
        "new_sum": 0,
        "new_avg": 0.0,
    }

# DELETA TODOS OS RATINGS DE UM USUÁRIO
@router.delete("/ratings/user/{user_id}", status_code=200)
def delete_all_ratings_from_user(user_id: str):

    pattern = f"rating:movie:*:user:{user_id}"
    keys = redis.keys(pattern)

    affected_movies = {}

    for key in keys:
        parts = key.split(":")
        # rating:movie:{movie_id}:user:{user_id}
        movie_id = parts[2]

        data = redis.hgetall(key)
        prev_score = int(data.get("score", 0)) if data else 0

        # remover rating
        redis.delete(key)

        # atualizar agregados do filme
        ckey = f"movie:{movie_id}:rating_count"
        skey = f"movie:{movie_id}:rating_sum"

        pipe = redis.pipeline()
        pipe.decr(ckey)
        pipe.decrby(skey, prev_score)
        pipe.get(ckey)
        pipe.get(skey)
        res = pipe.execute()

        new_count = int(res[-2] or 0)
        new_sum = int(res[-1] or 0)
        new_avg = (new_sum / new_count) if new_count > 0 else 0.0

        # atualizar leaderboard
        redis.zadd("top:avg_ratings", {movie_id: new_avg})

        affected_movies[movie_id] = {
            "new_count": new_count,
            "new_sum": new_sum,
            "new_avg": new_avg,
        }

    return {
        "message": "Todos os ratings do usuário foram removidos.",
        "user_id": user_id,
        "affected_movies": affected_movies,
    }

# DELETA TODAS AS RATINGS
@router.delete("/ratings/all", status_code=200)
def delete_all_ratings():
    # apaga ratings, agregados, leaderboard
    for key in redis.keys("rating:*"):
        redis.delete(key)

    for key in redis.keys("movie:*:rating_*"):
        redis.delete(key)

    redis.delete("top:avg_ratings")

    return {"ok": True, "deleted": "all ratings"}


api.include_router(router)