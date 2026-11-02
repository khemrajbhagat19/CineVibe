import os
import shutil
from pathlib import Path
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session
from ..config import settings
from ..database import get_db
from ..deps import get_admin_user
from ..models import Movie, User
from ..schemas import MovieCreate, MovieOut
from ..services.video import ALLOWED_IMAGE, ALLOWED_VIDEO, VideoError, new_name, process, safe_ext, thumbnail
from .movies import serialize

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats")
def stats(_: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    return {
        "movies": db.scalar(select(func.count(Movie.id))) or 0,
        "users": db.scalar(select(func.count(User.id))) or 0,
        "views": db.scalar(select(func.coalesce(func.sum(Movie.views), 0))) or 0,
        "genres": db.scalar(select(func.count(func.distinct(Movie.genre)))) or 0,
    }


@router.get("/movies", response_model=list[MovieOut])
def admin_movies(_: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    return [serialize(x) for x in db.scalars(select(Movie).order_by(desc(Movie.created_at))).all()]


@router.post("/movies", response_model=MovieOut)
async def upload_movie(
    title: str = Form(...),
    description: str = Form(""),
    genre: str = Form(...),
    release_year: int = Form(...),
    video: UploadFile = File(...),
    thumbnail_file: UploadFile | None = File(None),
    _: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    if not title.strip() or not genre.strip() or not 1888 <= release_year <= 2100:
        raise HTTPException(400, "Invalid movie metadata")
    try:
        video_ext = safe_ext(video.filename or "", ALLOWED_VIDEO)
        thumb_ext = safe_ext(thumbnail_file.filename, ALLOWED_IMAGE) if thumbnail_file and thumbnail_file.filename else None
    except VideoError as exc:
        raise HTTPException(400, str(exc)) from exc

    media_movies = Path(settings.media_root) / "movies"
    media_thumbs = Path(settings.media_root) / "thumbnails"
    media_movies.mkdir(parents=True, exist_ok=True)
    media_thumbs.mkdir(parents=True, exist_ok=True)

    token = new_name(video_ext).rsplit(".", 1)[0]
    temp_path = media_movies / f"{token}.upload{video_ext}"
    final_path = media_movies / f"{token}.mp4"
    thumb_name = f"{token}{thumb_ext or '.jpg'}"
    thumb_path = media_thumbs / thumb_name

    try:
        total_size = 0
        with temp_path.open("wb") as out:
            while True:
                chunk = await video.read(1024 * 1024)
                if not chunk:
                    break
                total_size += len(chunk)
                if total_size > settings.max_upload_size:
                    raise HTTPException(413, f"Video exceeds the {settings.max_upload_size // (1024 * 1024)} MB upload limit")
                out.write(chunk)
        duration = process(str(temp_path), str(final_path))
        if thumbnail_file:
            with thumb_path.open("wb") as out:
                image_size = 0
                while True:
                    chunk = await thumbnail_file.read(256 * 1024)
                    if not chunk:
                        break
                    image_size += len(chunk)
                    if image_size > 10 * 1024 * 1024:
                        raise HTTPException(413, "Poster image exceeds 10 MB")
                    out.write(chunk)
        else:
            thumbnail(str(final_path), str(thumb_path), duration)

        movie = Movie(
            title=title.strip()[:200], description=description.strip(),
            genre=genre.strip()[:80], release_year=release_year,
            duration_seconds=duration, video_filename=final_path.name,
            thumbnail_filename=thumb_path.name,
        )
        db.add(movie)
        db.commit()
        db.refresh(movie)
        return serialize(movie)
    except VideoError as exc:
        db.rollback()
        final_path.unlink(missing_ok=True)
        thumb_path.unlink(missing_ok=True)
        raise HTTPException(400, str(exc)) from exc
    except HTTPException:
        db.rollback()
        final_path.unlink(missing_ok=True)
        thumb_path.unlink(missing_ok=True)
        raise
    except Exception as exc:
        db.rollback()
        final_path.unlink(missing_ok=True)
        thumb_path.unlink(missing_ok=True)
        raise HTTPException(500, "Upload processing failed") from exc
    finally:
        temp_path.unlink(missing_ok=True)


@router.delete("/movies/{movie_id}")
def delete_movie(movie_id: int, _: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    movie = db.get(Movie, movie_id)
    if not movie:
        raise HTTPException(404, "Movie not found")
    video = Path(settings.media_root) / "movies" / movie.video_filename
    thumb = Path(settings.media_root) / "thumbnails" / (movie.thumbnail_filename or "")
    db.delete(movie)
    db.commit()
    video.unlink(missing_ok=True)
    thumb.unlink(missing_ok=True)
    return {"ok": True}


@router.patch("/users/{user_id}/status")
def toggle_user(user_id: int, _: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    user.is_active = not user.is_active
    db.commit()
    return {"id": user.id, "is_active": user.is_active}


@router.get("/users")
def users(_: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    return db.scalars(select(User).order_by(desc(User.created_at))).all()
