from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from .db import Base, engine, SessionLocal
from .models import User
from .schemas import UserCreate, UserOut, UserUpdate

api = FastAPI(title="users-service")

@api.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@api.post("/users", response_model=UserOut, status_code=201)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="email already exists")
    user = User(name=payload.name, email=payload.email)
    db.add(user); db.commit(); db.refresh(user)
    return user

@api.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: str, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="not found")
    return user

@api.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), limit: int = 20, offset: int = 0):
    items = db.query(User).order_by(User.created_at.desc()).limit(limit).offset(offset).all()
    return items

@api.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: str, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="not found")
    db.delete(user); db.commit()

@api.put("/users/{user_id}", response_model=UserOut)
def update_user(user_id: str, payload: UserUpdate, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="not found")

    # Verifica duplicidade
    if payload.email and payload.email != user.email:
        if db.query(User).filter(User.email == payload.email).first():
            raise HTTPException(status_code=409, detail="email already exists")

    # Atualiza apenas campos enviados
    if payload.name is not None:
        user.name = payload.name

    if payload.email is not None:
        user.email = payload.email

    db.commit()
    db.refresh(user)

    return user