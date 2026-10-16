import subprocess
import sys

from app.tasks import celery


def configure():
    celery.conf.update(
        task_default_queue="acceptance15",
        task_default_exchange="acceptance15",
        task_default_routing_key="acceptance15",
    )


if __name__ == "__main__":
    configure()
    if sys.argv[1] == "api":
        import uvicorn
        subprocess.run(["alembic", "upgrade", "head"], check=True)
        uvicorn.run("app.main:app", host="0.0.0.0", port=8000)
    elif sys.argv[1] == "worker":
        celery.worker_main([
            "worker", "--queues=acceptance15", "--hostname=acceptance15@%h",
            "--beat", "--schedule=/acceptance-media/celerybeat-schedule",
            "--loglevel=INFO", "--concurrency=2",
        ])
    else:
        raise SystemExit("Unknown acceptance role")
