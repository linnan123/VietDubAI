import json
import os

from fastapi import Depends, FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select

from .db import get_db
from .models import Episode, Job, Project
from .middleware import UploadBodyLimit
from .repositories import Repository
from .services import upload_media

app = FastAPI(title="VietDub AI", version="0.1.0")
app.add_middleware(UploadBodyLimit)
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","), allow_methods=["GET", "POST", "PATCH", "DELETE"], allow_headers=["Content-Type"])


class NameInput(BaseModel):
    name: str = Field(min_length=1, max_length=200, pattern=r"\S")


class ProjectInput(NameInput):
    description: str = Field(default="", max_length=5000)


class ProjectOutput(ProjectInput):
    model_config = ConfigDict(from_attributes=True)
    id: str


class EpisodeOutput(NameInput):
    model_config = ConfigDict(from_attributes=True)
    id: str
    project_id: str
    source_sha256: str | None
    metadata_json: str | None
    approved: bool


class JobOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    episode_id: str
    status: str
    attempts: int
    error: str | None
    created_at: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/projects", response_model=list[ProjectOutput])
def projects(db=Depends(get_db)):
    return Repository(db, Project).list()


@app.post("/projects", response_model=ProjectOutput, status_code=201)
def create_project(body: ProjectInput, db=Depends(get_db)):
    return Repository(db, Project).create(**body.model_dump())


@app.get("/projects/{identifier}", response_model=ProjectOutput)
def get_project(identifier: str, db=Depends(get_db)):
    return Repository(db, Project).get(identifier)


@app.patch("/projects/{identifier}", response_model=ProjectOutput)
def update_project(identifier: str, body: ProjectInput, db=Depends(get_db)):
    item = Repository(db, Project).get(identifier)
    item.name, item.description = body.name, body.description
    db.commit()
    return item


@app.delete("/projects/{identifier}", status_code=204)
def delete_project(identifier: str, db=Depends(get_db)):
    item = Repository(db, Project).get(identifier)
    if Repository(db, Episode).list(project_id=identifier):
        raise HTTPException(409, "Delete episodes first")
    db.delete(item)
    db.commit()


@app.get("/projects/{identifier}/episodes", response_model=list[EpisodeOutput])
def episodes(identifier: str, db=Depends(get_db)):
    Repository(db, Project).get(identifier)
    return Repository(db, Episode).list(project_id=identifier)


@app.post("/projects/{identifier}/episodes", response_model=EpisodeOutput, status_code=201)
def create_episode(identifier: str, body: NameInput, db=Depends(get_db)):
    Repository(db, Project).get(identifier)
    return Repository(db, Episode).create(project_id=identifier, name=body.name)


@app.get("/episodes/{identifier}", response_model=EpisodeOutput)
def get_episode(identifier: str, db=Depends(get_db)):
    return Repository(db, Episode).get(identifier)


@app.patch("/episodes/{identifier}", response_model=EpisodeOutput)
def update_episode(identifier: str, body: NameInput, db=Depends(get_db)):
    item = Repository(db, Episode).get(identifier)
    item.name = body.name
    db.commit()
    return item


@app.delete("/episodes/{identifier}", status_code=204)
def delete_episode(identifier: str, db=Depends(get_db)):
    item = Repository(db, Episode).get(identifier)
    jobs = Repository(db, Job).list(episode_id=identifier)
    if any(job.status in ("queued", "running") for job in jobs):
        raise HTTPException(409, "Wait for media processing to finish")
    for job in jobs:
        db.delete(job)
    db.flush()
    db.delete(item)
    db.commit()


@app.post("/episodes/{identifier}/upload", response_model=JobOutput, status_code=202)
async def upload(identifier: str, file: UploadFile, db=Depends(get_db)):
    return await upload_media(db, Repository(db, Episode).get(identifier), file)


@app.get("/jobs", response_model=list[JobOutput])
def jobs(db=Depends(get_db)):
    return db.scalars(select(Job).order_by(Job.created_at.desc()).limit(100)).all()


@app.get("/jobs/{identifier}", response_model=JobOutput)
def get_job(identifier: str, db=Depends(get_db)):
    return Repository(db, Job).get(identifier)


@app.post("/jobs/{identifier}/retry", response_model=JobOutput)
def retry(identifier: str, db=Depends(get_db)):
    item = Repository(db, Job).get(identifier)
    if item.status != "failed":
        raise HTTPException(409, "Only failed jobs can be retried")
    item.status, item.error = "queued", None
    db.commit()
    return item


@app.post("/episodes/{identifier}/approve", response_model=EpisodeOutput)
def approve(identifier: str, db=Depends(get_db)):
    item = Repository(db, Episode).get(identifier)
    job = db.scalar(select(Job).where(Job.episode_id == identifier))
    if not job or job.status != "succeeded" or not json.loads(item.metadata_json or "{}"):
        raise HTTPException(409, "Successful media analysis is required")
    item.approved = True
    db.commit()
    return item
