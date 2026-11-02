from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import get_current_user
from ..models import Movie, User, WatchHistory
from ..schemas import MovieOut, ProfileUpdate
from .movies import serialize

router = APIRouter(prefix="/users/me", tags=["users"])


@router.get("/history")
def history(user=Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(WatchHistory).where(WatchHistory.user_id == user.id).order_by(desc(WatchHistory.updated_at))).all()
    return [{"progress": r.progress, "updated_at": r.updated_at, "movie": serialize(r.movie).model_dump()} for r in rows]


@router.patch("/history/{movie_id}")
def progress(movie_id: int, payload: dict, user=Depends(get_current_user), db: Session = Depends(get_db)):
    movie = db.get(Movie, movie_id)
    if not movie:
        raise HTTPException(404, "Movie not found")
    value = max(0.0, min(100.0, float(payload.get("progress", 0))))
    row = db.scalar(select(WatchHistory).where(WatchHistory.user_id == user.id, WatchHistory.movie_id == movie_id))
    if not row:
        row = WatchHistory(user_id=user.id, movie_id=movie_id)
        db.add(row)
    row.progress = value
    db.commit()
    return {"ok": True, "progress": value}


@router.get("/profile")
def profile(user=Depends(get_current_user)):
    return {"id": user.id, "name": user.name, "email": user.email, "is_admin": user.is_admin}


@router.patch("/profile")
def update_profile(payload: ProfileUpdate, user=Depends(get_current_user), db: Session = Depends(get_db)):
    user.name = payload.name.strip()
    db.commit()
    db.refresh(user)
    return user
