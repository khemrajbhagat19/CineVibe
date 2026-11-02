# Antigravity implementation prompt

You are an expert full-stack engineer. Work directly on the existing uploaded CineVibe streaming project and transform it into a production-oriented full-stack streaming platform.

## First: audit the existing code

Before changing anything:
- Read every source file.
- Understand the current Flask routes, SQLAlchemy models, templates, CSS, JavaScript, authentication, admin flow, FFmpeg processing, thumbnail generation, HTTP Range streaming, and watch-progress implementation.
- Preserve the useful product behavior from the existing project.
- Do not blindly rewrite working logic without checking dependencies and edge cases.

The existing project already contains the right product foundation:
- Movie catalog
- Search/filter/sort
- Login/register
- Admin dashboard
- Admin upload/edit/delete
- FFmpeg conversion to browser-friendly MP4
- Thumbnail generation
- HTTP Range streaming
- Watch history
- Resume playback

## Target architecture

Refactor the project into:

Frontend:
- React
- Vite
- React Router
- Axios
- Responsive dark cinematic UI

Backend:
- FastAPI
- SQLAlchemy
- PostgreSQL
- JWT authentication
- bcrypt password hashing
- REST API
- Role-based admin authorization

Media:
- FFmpeg + ffprobe
- Persistent Docker volume for local development/deployment
- HTTP Range support for MP4 streaming
- Validate file extensions and MIME types
- Generate thumbnails automatically when no poster is supplied

Infrastructure:
- Docker
- Docker Compose
- Nginx reverse proxy
- PostgreSQL persistent volume
- Media persistent volume
- Environment variables for secrets/configuration

## Required API

Implement and document:

Public:
- GET /api/health
- GET /api/movies
- GET /api/movies/{id}
- GET /api/movies/{id}/stream
- GET /api/movies/{id}/thumbnail
- GET /api/movies/meta/genres

Auth:
- POST /api/auth/register
- POST /api/auth/login
- GET /api/auth/me

User:
- GET /api/users/me/history
- POST /api/movies/{id}/progress
- GET /api/users/me/profile
- PATCH /api/users/me/profile

Admin:
- GET /api/admin/stats
- GET /api/admin/movies
- POST /api/admin/movies
- DELETE /api/admin/movies/{id}
- GET /api/admin/users
- PATCH /api/admin/users/{id}/status

## Streaming requirements

The video endpoint must support:
- Range requests
- 206 Partial Content
- Accept-Ranges
- Content-Length
- Content-Range
- Seeking
- Browser HTML5 video playback
- Streaming without loading the whole file into RAM

Do not read the complete video into memory.

For the first version, process uploads into H.264/AAC MP4 with `+faststart`.

## Security requirements

- Never hard-code production secrets.
- Use `.env`.
- Hash passwords with bcrypt.
- Use JWT expiration.
- Protect admin endpoints by role.
- Validate upload extensions.
- Generate random server-side media filenames.
- Prevent path traversal.
- Do not expose filesystem paths in API responses.
- Add CORS configuration from environment.
- Limit upload size.
- Never allow a normal user to call admin APIs.
- Return useful HTTP errors.

## Frontend requirements

Create:
1. Home page with cinematic hero.
2. Movie library.
3. Search.
4. Genre filter.
5. Sort by latest/views/A-Z.
6. Movie details.
7. Full-screen-friendly video player.
8. Resume playback.
9. Watch history.
10. Login.
11. Registration.
12. Admin dashboard.
13. Movie upload with poster.
14. Movie deletion.
15. User status management.

UI should be:
- Premium
- Modern
- Responsive
- Dark/cinematic
- Mobile-friendly
- Clean cards
- Smooth hover effects
- Good loading and empty states
- No childish design
- Accessible buttons/forms
- Error handling

## Docker requirements

Provide:
- backend/Dockerfile
- frontend/Dockerfile
- docker-compose.yml
- frontend/nginx.conf
- .env.example
- .gitignore
- README
- deployment documentation

`docker compose up --build` should start:
- PostgreSQL
- FastAPI backend
- React frontend
- Nginx

The frontend must call `/api/...` so Nginx can proxy API requests to the backend.

Use Docker volumes for:
- PostgreSQL
- media uploads

Do not put `.env`, database files, uploaded videos, node_modules, or virtual environments in Git.

## Important production evolution

Keep the architecture ready for:
- S3/MinIO object storage
- CDN
- HLS multi-bitrate streaming
- Redis
- Celery/RQ/Dramatiq
- background transcoding jobs
- Alembic migrations
- rate limiting
- signed video URLs
- analytics

Do not introduce these dependencies unless necessary for the current runnable build. Document where they should be added when scaling.

## Validation

After implementation:
- Run Python syntax checks.
- Run frontend build.
- Start Docker Compose.
- Verify `/api/health`.
- Verify register/login.
- Verify admin authorization.
- Verify movie upload.
- Verify FFmpeg processing.
- Verify thumbnail generation.
- Verify video seeking with Range requests.
- Verify progress saving.
- Verify movie deletion removes the database record and media files.
- Check responsive UI.

If something fails, fix the root cause instead of hiding the error.

## Final deliverable

The final project must be runnable from the repository root with:

```bash
docker compose up --build
```

and available at:

```text
http://localhost
```

Use the project name **CineVibe** consistently. Do not rename it to KarmDhatu or any HRMS product name.
