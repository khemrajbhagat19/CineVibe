import os
import re
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, Response, StreamingResponse
from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session
from ..config import settings
from ..database import get_db
from ..deps import get_current_user
from ..models import Movie, WatchHistory
from ..schemas import MovieOut, ProgressUpdate

router = APIRouter(prefix="/movies", tags=["movies"])


def serialize(movie: Movie) -> MovieOut:
    return MovieOut(
        id=movie.id, title=movie.title, description=movie.description,
        genre=movie.genre, release_year=movie.release_year,
        duration_seconds=movie.duration_seconds, views=movie.views,
        created_at=movie.created_at,
        thumbnail_url=f"/api/movies/{movie.id}/thumbnail",
        stream_url=f"/api/movies/{movie.id}/stream",
    )


@router.get("", response_model=list[MovieOut])
def list_movies(
    search: str = "",
    genre: str = "",
    year: int | None = None,
    sort: str = "latest",
    db: Session = Depends(get_db),
):
    q = select(Movie)
    if search:
        term = f"%{search.strip()}%"
        q = q.where(or_(Movie.title.ilike(term), Movie.genre.ilike(term), Movie.description.ilike(term)))
    if genre:
        q = q.where(Movie.genre == genre)
    if year:
        q = q.where(Movie.release_year == year)
    if sort == "views":
        q = q.order_by(desc(Movie.views))
    elif sort == "az":
        q = q.order_by(Movie.title.asc())
    else:
        q = q.order_by(desc(Movie.created_at))
    return [serialize(x) for x in db.scalars(q.limit(100)).all()]


@router.get("/meta/genres")
def genres(db: Session = Depends(get_db)):
    return sorted(db.scalars(select(Movie.genre).distinct()).all())


@router.get("/{movie_id}", response_model=MovieOut)
def movie(movie_id: int, db: Session = Depends(get_db)):
    item = db.get(Movie, movie_id)
    if not item:
        raise HTTPException(404, "Movie not found")
    return serialize(item)


def _file_path(movie: Movie) -> str:
    return os.path.join(settings.media_root, "movies", movie.video_filename)


@router.get("/{movie_id}/thumbnail")
def thumbnail(movie_id: int, db: Session = Depends(get_db)):
    item = db.get(Movie, movie_id)
    if not item or not item.thumbnail_filename:
        raise HTTPException(404, "Thumbnail not found")
    path = os.path.join(settings.media_root, "thumbnails", item.thumbnail_filename)
    if not os.path.isfile(path):
        raise HTTPException(404, "Thumbnail file missing")
    return FileResponse(path, media_type="image/jpeg")


@router.get("/{movie_id}/stream")
def stream(movie_id: int, request: Request, db: Session = Depends(get_db)):
    item = db.get(Movie, movie_id)
    if not item:
        raise HTTPException(404, "Movie not found")
    path = _file_path(item)
    if not os.path.isfile(path):
        raise HTTPException(404, "Video file missing")

    size = os.path.getsize(path)
    range_header = request.headers.get("range")
    start, end = 0, size - 1
    status = 200

    if range_header:
        match = re.fullmatch(r"bytes=(\d*)-(\d*)", range_header.strip())
        if not match:
            return Response(status_code=416, headers={"Content-Range": f"bytes */{size}"})
        a, b = match.groups()
        if a == "":
            start = max(size - int(b), 0)
        else:
            start = int(a)
            if b:
                end = min(int(b), size - 1)
        if start > end or start >= size:
            return Response(status_code=416, headers={"Content-Range": f"bytes */{size}"})
        status = 206

    length = end - start + 1

    def iterator(chunk_size=1024 * 1024):
        with open(path, "rb") as f:
            f.seek(start)
            remaining = length
            while remaining:
                data = f.read(min(chunk_size, remaining))
                if not data:
                    break
                remaining -= len(data)
                yield data

    headers = {
        "Accept-Ranges": "bytes",
        "Content-Length": str(length),
        "Cache-Control": "private, max-age=3600",
        "Content-Type": "video/mp4",
    }
    if status == 206:
        headers["Content-Range"] = f"bytes {start}-{end}/{size}"

    return StreamingResponse(iterator(), status_code=status, headers=headers, media_type="video/mp4")


@router.post("/{movie_id}/view")
def add_view(movie_id: int, db: Session = Depends(get_db)):
    item = db.get(Movie, movie_id)
    if not item:
        raise HTTPException(404, "Movie not found")
    item.views += 1
    db.commit()
    return {"views": item.views}


@router.post("/{movie_id}/progress")
def save_progress(movie_id: int, payload: ProgressUpdate, user=Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.get(Movie, movie_id)
    if not item:
        raise HTTPException(404, "Movie not found")
    history = db.scalar(select(WatchHistory).where(WatchHistory.user_id == user.id, WatchHistory.movie_id == movie_id))
    if not history:
        history = WatchHistory(user_id=user.id, movie_id=movie_id)
        db.add(history)
    history.progress = payload.progress
    db.commit()
    return {"ok": True, "progress": history.progress}
