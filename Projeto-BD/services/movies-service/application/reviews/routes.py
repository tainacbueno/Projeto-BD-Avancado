from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from bson import ObjectId
from datetime import datetime, timezone
from ..db import reviews

router = APIRouter()

class ReviewIn(BaseModel):
    user_id: str
    movie_id: str
    text: str

def oid(s: str):
    try: return ObjectId(s)
    except: raise HTTPException(400, "invalid id")

@router.post("/", status_code=201)
def create_review(rin: ReviewIn):
    doc = rin.model_dump()
    doc["created_at"] = datetime.now(timezone.utc)
    r = reviews.insert_one(doc)
    saved = reviews.find_one({"_id": r.inserted_id})
    saved["id"] = str(saved.pop("_id"))
    return saved

@router.get("/{review_id}")
def get_movie(review_id: str):
    doc = reviews.find_one({"_id": oid(review_id)})
    if not doc: raise HTTPException(404, "not found")
    doc["id"] = str(doc.pop("_id"))
    return doc

@router.get("/")
def list_reviews(movie_id: str | None = None, user_id: str | None = None, q: str | None = None,
                 limit: int = 20, skip: int = 0):
    query = {}
    if movie_id: query["movie_id"] = movie_id
    if user_id: query["user_id"] = user_id
    if q: query["$text"] = {"$search": q}
    cursor = reviews.find(query).skip(skip).limit(limit).sort("created_at", -1)
    result = []
    for d in cursor:
        d["id"] = str(d.pop("_id"))
        result.append(d)
    return result

@router.delete("/{review_id}", status_code=204)
def delete_review(review_id: str):
    res = reviews.delete_one({"_id": oid(review_id)})
    if res.deleted_count == 0:
        raise HTTPException(404, "not found")


# DELETA TODOS OS REVIEWS
@router.delete("/reviews/all", status_code=200)
def delete_all_reviews():
    reviews.delete_many({})
    return {"ok": True, "deleted": "all reviews"}