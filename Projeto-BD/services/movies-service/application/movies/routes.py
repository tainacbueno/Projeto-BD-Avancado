from fastapi import APIRouter, HTTPException
from bson import ObjectId
from ..db import movies
from .schemas import MovieIn, MovieUpdate

router = APIRouter()

def oid(s: str):
    try: return ObjectId(s)
    except: raise HTTPException(400, "invalid id")

@router.post("/", status_code=201)
def create_movie(m: MovieIn):
    existing = movies.find_one({"title": m.title})
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"movie with title '{m.title}' already exists"
        )

    doc = m.model_dump()
    r = movies.insert_one(doc)
    saved = movies.find_one({"_id": r.inserted_id})
    saved["id"] = str(saved.pop("_id"))
    return saved

@router.get("/{movie_id}")
def get_movie(movie_id: str):
    doc = movies.find_one({"_id": oid(movie_id)})
    if not doc: raise HTTPException(404, "not found")
    doc["id"] = str(doc.pop("_id"))
    return doc

@router.get("/")
def list_movies(title: str | None = None, genre: str | None = None, year: int | None = None, limit: int = 20, skip: int = 0):
    query = {}

    if title: 
        query["$text"] = {"$search": title}
    if genre:
        query["genres"] = {"$in": [genre]}
    if year:
        query["year"] = year

    cursor = movies.find(query).skip(skip).limit(limit)
    res = []
    for d in cursor:
        d["id"] = str(d.pop("_id"))
        res.append(d)
    return res

@router.put("/{movie_id}")
def update_movie(movie_id: str, payload: MovieUpdate):
    _id = oid(movie_id)

    existing = movies.find_one({"_id": _id})
    if not existing:
        raise HTTPException(404, "not found")

    # Se atualizar título, verificar duplicidade
    if payload.title and payload.title != existing.get("title"):
        other = movies.find_one({"title": payload.title})
        if other:
            raise HTTPException(
                status_code=400,
                detail=f"movie with title '{payload.title}' already exists"
            )

    update_data = payload.model_dump(exclude_none=True)

    if not update_data:
        return {**existing, "id": movie_id}  # nada para atualizar

    movies.update_one({"_id": _id}, {"$set": update_data})

    updated = movies.find_one({"_id": _id})
    updated["id"] = str(updated.pop("_id"))
    return updated


@router.delete("/{movie_id}", status_code=204)
def delete_movie(movie_id: str):
    res = movies.delete_one({"_id": oid(movie_id)})
    if res.deleted_count == 0:
        raise HTTPException(404, "not found")


# DELETA TODOS OS FILMES
@router.delete("/movies/all", status_code=200)
def delete_all_movies():
    movies.delete_many({})
    return {"ok": True, "deleted": "all movies"}