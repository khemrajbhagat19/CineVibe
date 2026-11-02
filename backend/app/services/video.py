import json
import os
import subprocess
import uuid
from pathlib import Path


class VideoError(Exception):
    pass


ALLOWED_VIDEO = {".mp4", ".mkv", ".webm", ".mov", ".avi"}
ALLOWED_IMAGE = {".jpg", ".jpeg", ".png", ".webp"}


def _run(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
    except FileNotFoundError as exc:
        raise VideoError("FFmpeg/ffprobe is not installed.") from exc
    except subprocess.TimeoutExpired as exc:
        raise VideoError("Video processing timed out.") from exc


def probe(src: str) -> dict:
    result = _run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", src])
    if result.returncode != 0:
        raise VideoError("Uploaded file is not a valid video.")
    data = json.loads(result.stdout or "{}")
    video = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), None)
    audio = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), None)
    if not video:
        raise VideoError("Uploaded file has no video stream.")
    try:
        duration = int(float(data.get("format", {}).get("duration") or 0))
    except ValueError:
        duration = 0
    return {"duration": duration, "vcodec": video.get("codec_name"), "acodec": audio.get("codec_name") if audio else None}


def process(src: str, dest: str) -> int:
    info = probe(src)
    if info["vcodec"] == "h264" and info["acodec"] in (None, "aac", "mp3"):
        args = ["-c", "copy"]
    else:
        args = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
                "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k"]
    result = _run(["ffmpeg", "-y", "-v", "error", "-i", src, *args, "-movflags", "+faststart", dest])
    if result.returncode != 0 or not os.path.isfile(dest):
        raise VideoError(result.stderr[-500:] or "FFmpeg could not process the video.")
    return info["duration"]


def thumbnail(video: str, dest: str, duration: int):
    at = 5 if duration >= 10 else max(duration // 2, 0)
    result = _run(["ffmpeg", "-y", "-v", "error", "-ss", str(at), "-i", video,
                   "-frames:v", "1", "-q:v", "3", dest])
    if result.returncode != 0 or not os.path.isfile(dest):
        raise VideoError("Could not generate thumbnail.")


def safe_ext(filename: str, allowed: set[str]) -> str:
    ext = Path(filename or "").suffix.lower()
    if ext not in allowed:
        raise VideoError(f"Unsupported file type: {ext or 'unknown'}")
    return ext


def new_name(ext: str) -> str:
    return f"{uuid.uuid4().hex}{ext}"
