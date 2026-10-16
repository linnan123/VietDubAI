import hashlib
import os
import uuid

from fastapi import HTTPException
from sqlalchemy import update

from . import media
from .models import Episode, Job


async def upload_media(session, episode, upload):
    if not upload.filename or not upload.filename.lower().endswith(".mp4"):
        raise HTTPException(415, "Only MP4 uploads are accepted")
    if episode.source_path:
        raise HTTPException(409, "Source media is immutable; create another episode")
    directory = media.MEDIA_ROOT / episode.id
    directory.mkdir(parents=True, exist_ok=True)
    temporary = directory / f"{uuid.uuid4()}.part"
    source = directory / f"{uuid.uuid4()}.mp4"
    digest = hashlib.sha256()
    size = 0
    try:
        with temporary.open("xb") as output:
            while chunk := await upload.read(1024 * 1024):
                size += len(chunk)
                if size > media.MAX_UPLOAD_BYTES:
                    raise HTTPException(413, "Maximum upload size is 512 MiB")
                digest.update(chunk)
                output.write(chunk)
            output.flush()
            os.fsync(output.fileno())
        if size < 12:
            raise HTTPException(415, "Invalid MP4")
        with temporary.open("rb") as uploaded:
            if uploaded.read(12)[4:8] != b"ftyp":
                raise HTTPException(415, "Invalid MP4 signature")
        temporary.replace(source)
        result = session.execute(update(Episode).where(Episode.id == episode.id, Episode.source_path.is_(None)).values(source_path=str(source), source_sha256=digest.hexdigest()))
        if result.rowcount != 1:
            raise HTTPException(409, "Episode already has source media")
        job = Job(episode_id=episode.id)
        session.add(job)
        session.commit()
        return job
    except Exception:
        session.rollback()
        source.unlink(missing_ok=True)
        raise
    finally:
        temporary.unlink(missing_ok=True)
        await upload.close()
