# CineVibe Streaming Platform

A production-oriented full-stack movie/video streaming starter rebuilt from the uploaded CineVibe Flask project.

## What was preserved/improved from the uploaded project

The original project already had:
- Flask + SQLAlchemy authentication and admin roles
- Movie metadata and genre browsing
- FFmpeg/ffprobe processing
- H.264/AAC MP4 conversion
- Poster/thumbnail generation
- HTTP Range video streaming
- Watch history and resume progress
- Admin upload/edit/delete and user management
- A dark cinematic UI

This version keeps those core ideas but restructures the application into:
- **Frontend:** React + Vite
- **Backend/API:** FastAPI + SQLAlchemy
- **Database:** PostgreSQL in Docker, SQLite-compatible local configuration
- **Media:** persistent Docker volume
- **Video processing:** FFmpeg
- **Auth:** JWT access tokens + bcrypt password hashing
- **Streaming:** HTTP Range / 206 Partial Content
- **Reverse proxy:** Nginx
- **Deployment:** Docker Compose

## Quick start

1. Copy `.env.example` to `.env`.
2. Start everything:

```bash
docker compose up --build
```

3. Open:

```text
http://localhost
```

API health:

```text
http://localhost/api/health
```

Default admin:

```text
Email: admin@cinevibe.local
Password: ChangeMe@123
```

Change the credentials before production use.

## Project structure

```text
CineVibe_Streaming/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── auth.py
│   │   ├── deps.py
│   │   ├── api/
│   │   │   ├── auth.py
│   │   │   ├── movies.py
│   │   │   ├── users.py
│   │   │   └── admin.py
│   │   └── services/
│   │       └── video.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api.js
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── styles.css
│   ├── package.json
│   ├── vite.config.js
│   ├── nginx.conf
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── .gitignore
```

## API

### Public
- `GET /api/health`
- `GET /api/movies`
- `GET /api/movies/{id}`
- `GET /api/movies/{id}/stream`
- `GET /api/movies/{id}/thumbnail`

### Authentication
- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`

### User
- `GET /api/users/me/history`
- `POST /api/users/me/history/{movie_id}`
- `GET /api/users/me/profile`
- `PATCH /api/users/me/profile`

### Admin
- `GET /api/admin/stats`
- `GET /api/admin/movies`
- `POST /api/admin/movies`
- `PATCH /api/admin/movies/{id}`
- `DELETE /api/admin/movies/{id}`
- `GET /api/admin/users`
- `PATCH /api/admin/users/{id}/status`

## Production notes

This starter stores media on a Docker volume. For a real high-scale service, move media to S3-compatible object storage and put a CDN in front of it. The API should then issue signed media URLs rather than making the application server handle every byte.

The current upload endpoint intentionally processes a file synchronously to keep the project easy to understand. For high traffic, use a background job system (Celery/RQ/Dramatiq + Redis) and a job-status endpoint.

Only upload and stream content you have the legal right to distribute.

## Local Windows setup (no Docker)

### Backend

1. Open PowerShell in the `backend` folder.
2. Create and activate a virtual environment:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Install dependencies and create your local environment file:

```powershell
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

4. Edit `backend\.env` and replace `JWT_SECRET` with a long random secret. Change the admin password before using the app.
5. Ensure `ffmpeg -version` and `ffprobe -version` work in PowerShell.
6. Start the API:

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

API health: `http://127.0.0.1:8001/api/health`  
API docs: `http://127.0.0.1:8001/docs`

### Frontend (open a second PowerShell window)

```powershell
cd "C:\path\to\CineVibe_Streaming_Docker_Ready\frontend"
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.
The Vite development proxy forwards `/api` requests to `http://127.0.0.1:8001`. Keep both terminals running. If port 5173 is already occupied, find its actual PID using `netstat -ano | findstr :5173`, then stop that PID (not an example PID) or close the existing Vite terminal.

Default admin account is created on first backend startup from `backend/.env`: `admin@cinevibe.local`. Set a new password in that file before use. If an admin user already exists in the SQLite database, changing the environment password does not reset that existing account.
