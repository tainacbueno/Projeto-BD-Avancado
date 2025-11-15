from pymongo import MongoClient, ASCENDING, TEXT, DESCENDING
import os

MONGO_URL = os.getenv("MONGO_URL", "mongodb://mongo:27017")
MONGO_DB = os.getenv("MONGO_DB", "polyglot_movies")

client = MongoClient(MONGO_URL)
db = client[MONGO_DB]

movies = db["movies"]
reviews = db["reviews"]

def ensure_indexes():
    movies.create_index([("title", TEXT)])
    movies.create_index([("genres", ASCENDING)])
    movies.create_index([("year", ASCENDING)])
    reviews.create_index([("movie_id", ASCENDING), ("created_at", DESCENDING)])
    reviews.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
    reviews.create_index([("text", TEXT)])
