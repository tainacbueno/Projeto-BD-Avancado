from faker import Faker
from random import randint, sample, choice

fake = Faker("pt_BR")

GENRES = ["Action","Adventure","Animation","Comedy","Drama",
          "Fantasy","Family","Sci-Fi","Thriller"]

def fake_user():
    return {"name": fake.name(), "email": fake.unique.email()}

def fake_movie():
    g = sample(GENRES, k=randint(1, 3))
    cast = [{"name": fake.name(), "role": fake.job()} for _ in range(randint(2, 5))]
    return {
        "title": " ".join(fake.words(nb=randint(1, 3))).title(),
        "year": randint(1970, 2024),
        "genres": g,
        "cast": cast,
        "overview": fake.paragraph(nb_sentences=3),
        "runtime": randint(80, 160),
    }

def fake_review(user_id: str, movie_id: str):
    return {
        "user_id": user_id,
        "movie_id": movie_id,
        "text": choice([
            fake.paragraph(nb_sentences=2),
            fake.paragraph(nb_sentences=3),
            fake.sentence(nb_words=12)
        ])
    }

def fake_rating(user_id: str, movie_id: str):
    return {"user_id": user_id, "movie_id": movie_id, "score": randint(1, 5)}