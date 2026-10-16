import json
import os
import time
from pathlib import Path

from celery import Celery
from sqlalchemy import or_, select, update

from .db import Session
from .media import extract_wav, probe
from .models import Episode, Job

celery = Celery("vietdub", broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"))
celery.conf.update(task_acks_late=True, task_reject_on_worker_lost=True, broker_connection_retry_on_startup=True, beat_schedule={"recover-jobs": {"task": "app.tasks.dispatch", "schedule": 15.0}})


@celery.task
def dispatch():
    with Session() as session:
        identifiers = session.scalars(select(Job.id).where(or_(Job.status == "queued", (Job.status == "running") & (Job.lease_until < int(time.time()))))).all()
    for identifier in identifiers:
        process.delay(identifier)


@celery.task(soft_time_limit=1900, time_limit=1950)
def process(identifier):
    with Session() as session:
        claimed = session.execute(update(Job).where(Job.id == identifier, or_(Job.status == "queued", (Job.status == "running") & (Job.lease_until < int(time.time())))).values(status="running", lease_until=int(time.time()) + 2100, attempts=Job.attempts + 1, error=None))
        session.commit()
        if claimed.rowcount != 1:
            return
        job = session.get(Job, identifier)
        episode = session.get(Episode, job.episode_id)
        target = Path(episode.source_path).parent / "audio.wav"
        temporary = target.with_name("audio.part.wav")
        try:
            metadata = probe(Path(episode.source_path))
            extract_wav(Path(episode.source_path), temporary)
            temporary.replace(target)
            episode.metadata_json = json.dumps(metadata)
            episode.wav_path = str(target)
            job.status = "succeeded"
        except Exception as error:
            job.status = "failed"
            job.error = f"Media processing failed ({type(error).__name__}); verify MP4 streams and FFmpeg installation."
        finally:
            temporary.unlink(missing_ok=True)
        session.commit()
