from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from .api import auth, movies, users, admin
from .auth import hash_password
from .config import settings
from .database import Base, SessionLocal, engine
from .models import User

@asynccontextmanager
async def lifespan(app: FastAPI):
    Path(settings.media_root, "movies").mkdir(parents=True, exist_ok=True)
    Path(settings.media_root, "thumbnails").mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        email = settings.admin_email.lower().strip()
        if not db.scalar(select(User).where(User.email == email)):
            db.add(User(name="CineVibe Admin", email=email,
                        password_hash=hash_password(settings.admin_password), is_admin=True))
            db.commit()
    finally:
        db.close()
    yield

app = FastAPI(title="CineVibe Streaming API", version="2.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_list, allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])
app.include_router(auth.router, prefix="/api")
app.include_router(movies.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(admin.router, prefix="/api")

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "cinevibe-api"}
