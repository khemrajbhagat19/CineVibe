# Docker deployment checklist

## 1. Prepare

```bash
cp .env.example .env
```

Generate a strong JWT secret:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Put that value in `.env` as `JWT_SECRET`.

Use a strong PostgreSQL password and update both `POSTGRES_PASSWORD` and the password embedded in `DATABASE_URL`.

## 2. Start

```bash
docker compose up -d --build
```

## 3. Check

```bash
docker compose ps
docker compose logs -f backend
```

Open `http://YOUR_SERVER_IP/`.

## 4. HTTPS

For production, put a TLS reverse proxy such as Caddy, Traefik or an external load balancer in front of the Nginx service. Do not expose PostgreSQL directly.

## 5. Persistent data

The stack creates:
- `postgres_data` for database data
- `media_data` for uploaded/processed video and thumbnails

Back up both volumes.

## 6. Scaling recommendation

For a larger streaming service:
1. Object storage (S3/MinIO) for video.
2. CDN for delivery.
3. Redis + Celery/RQ for FFmpeg jobs.
4. HLS/DASH transcoding into multiple resolutions.
5. Signed URLs and entitlement checks.
6. Database migrations with Alembic.
7. Observability and rate limiting.
