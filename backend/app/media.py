import json
import os
import subprocess
from pathlib import Path

MEDIA_ROOT = Path(os.getenv("MEDIA_ROOT", "./data")).resolve()
MAX_UPLOAD_BYTES = 512 * 1024 * 1024


def probe(path: Path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-protocol_whitelist", "file", "-show_format", "-show_streams", "-of", "json", str(path)],
        capture_output=True, text=True, timeout=60, check=True,
    )
    data = json.loads(result.stdout)
    streams = data.get("streams", [])
    if "mp4" not in data.get("format", {}).get("format_name", ""):
        raise ValueError("Container must be MP4")
    video = next((stream for stream in streams if stream["codec_type"] == "video"), None)
    if video is None or not any(stream["codec_type"] == "audio" for stream in streams):
        raise ValueError("MP4 must contain video and audio")
    duration_ms = round(float(data["format"]["duration"]) * 1000)
    if duration_ms <= 0 or duration_ms > 6 * 60 * 60 * 1000:
        raise ValueError("Duration must be between 0 and 6 hours")
    return {"duration_ms": duration_ms, "width": video["width"], "height": video["height"], "video_codec": video["codec_name"]}


def extract_wav(source: Path, target: Path):
    subprocess.run(
        ["ffmpeg", "-nostdin", "-v", "error", "-protocol_whitelist", "file", "-i", str(source), "-vn", "-map", "0:a:0", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", "-y", str(target)],
        capture_output=True, timeout=1800, check=True,
    )
