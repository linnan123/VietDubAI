import io
import json
import shutil
import subprocess
import wave

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import media, tasks
from app.db import Base, get_db
from app.main import app
from app.models import Episode, Job


@pytest.fixture
def client(tmp_path, monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    def database():
        with factory() as session:
            yield session
    app.dependency_overrides[get_db] = database
    monkeypatch.setattr(media, "MEDIA_ROOT", tmp_path)
    monkeypatch.setattr(tasks, "Session", factory)
    with TestClient(app) as connection:
        yield connection
    app.dependency_overrides.clear()
    engine.dispose()


def episode(client):
    project = client.post("/projects", json={"name": "Drama"}).json()
    return client.post(f"/projects/{project['id']}/episodes", json={"name": "01"}).json()


def upload(client, identifier, name="video.mp4", content=b"\x00\x00\x00\x18ftypisomtest"):
    return client.post(f"/episodes/{identifier}/upload", files={"file": (name, io.BytesIO(content), "video/mp4")})


def test_crud(client):
    item = episode(client)
    project_id, identifier = item["project_id"], item["id"]
    assert len(client.get("/projects").json()) == 1
    assert client.get(f"/projects/{project_id}").status_code == 200
    assert client.patch(f"/projects/{project_id}", json={"name": "Updated"}).json()["name"] == "Updated"
    assert client.delete(f"/projects/{project_id}").status_code == 409
    assert client.patch(f"/episodes/{identifier}", json={"name": "02"}).json()["name"] == "02"
    assert len(client.get(f"/projects/{project_id}/episodes").json()) == 1
    assert client.delete(f"/episodes/{identifier}").status_code == 204
    assert client.delete(f"/projects/{project_id}").status_code == 204
    assert client.get(f"/episodes/{identifier}").status_code == 404


def test_validation(client):
    assert client.post("/projects", json={"name": " "}).status_code == 422
    assert client.post("/projects/missing/episodes", json={"name": "01"}).status_code == 404
    identifier = episode(client)["id"]
    assert upload(client, identifier, "video.txt").status_code == 415
    assert upload(client, identifier, content=b"invalid data payload").status_code == 415
    assert client.post(f"/episodes/{identifier}/approve").status_code == 409


def test_size_limit(client, monkeypatch):
    monkeypatch.setattr(media, "MAX_UPLOAD_BYTES", 8)
    assert upload(client, episode(client)["id"]).status_code == 413
    assert not list(media.MEDIA_ROOT.rglob("*.part"))


def test_request_body_limit(client, monkeypatch):
    monkeypatch.setattr(media, "MAX_UPLOAD_BYTES", 8)
    identifier = episode(client)["id"]
    assert upload(client, identifier, content=bytes(1024 * 1024 + 9)).status_code == 413


def test_upload_immutable_and_idempotent_job(client, monkeypatch):
    identifier = episode(client)["id"]
    response = upload(client, identifier, "../../video.mp4")
    assert response.status_code == 202
    job = response.json()
    assert upload(client, identifier).status_code == 409
    assert client.delete(f"/episodes/{identifier}").status_code == 409
    calls = []
    monkeypatch.setattr(tasks, "probe", lambda path: {"duration_ms": 1200, "width": 100, "height": 200})
    def extract(source, target):
        calls.append(source)
        target.write_bytes(b"mock wav")
    monkeypatch.setattr(tasks, "extract_wav", extract)
    tasks.process.run(job["id"])
    tasks.process.run(job["id"])
    assert len(calls) == 1
    assert client.get(f"/jobs/{job['id']}").json()["status"] == "succeeded"
    result = client.post(f"/episodes/{identifier}/approve")
    assert result.json()["approved"] is True
    assert json.loads(result.json()["metadata_json"])["duration_ms"] == 1200
    assert client.post(f"/jobs/{job['id']}/retry").status_code == 409


def test_failed_job_retry_and_recovery(client, monkeypatch):
    identifier = episode(client)["id"]
    job = upload(client, identifier).json()
    def fail(path):
        raise ValueError("malformed")
    monkeypatch.setattr(tasks, "probe", fail)
    tasks.process.run(job["id"])
    assert client.get(f"/jobs/{job['id']}").json()["status"] == "failed"
    assert client.post(f"/jobs/{job['id']}/retry").json()["status"] == "queued"
    with tasks.Session() as session:
        record = session.get(Job, job["id"])
        record.status, record.lease_until = "running", 0
        session.commit()
    queued = []
    monkeypatch.setattr(tasks.process, "delay", queued.append)
    tasks.dispatch.run()
    assert queued == [job["id"]]
    tasks.process.run(job["id"])
    assert client.get(f"/jobs/{job['id']}").json()["attempts"] == 2


def test_probe_rejects_non_mp4_and_missing_audio(monkeypatch, tmp_path):
    class Result:
        stdout = json.dumps({"format": {"format_name": "mp4", "duration": "1"}, "streams": [{"codec_type": "video"}]})
    monkeypatch.setattr(media.subprocess, "run", lambda *args, **kwargs: Result())
    with pytest.raises(ValueError, match="video and audio"):
        media.probe(tmp_path / "video.mp4")


@pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"), reason="FFmpeg / FFprobe not installed")
def test_real_media_pipeline(client):
    source = media.MEDIA_ROOT / "fixture.mp4"
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i", "color=c=black:s=160x120:d=1", "-f", "lavfi", "-i", "sine=frequency=440:duration=1", "-c:v", "mpeg4", "-c:a", "aac", "-shortest", str(source)], check=True, timeout=30)
    identifier = episode(client)["id"]
    job = upload(client, identifier, content=source.read_bytes()).json()
    tasks.process.run(job["id"])
    assert client.get(f"/jobs/{job['id']}").json()["status"] == "succeeded"
    with wave.open(str(media.MEDIA_ROOT / identifier / "audio.wav")) as audio:
        assert audio.getframerate() == 16000
        assert audio.getnchannels() == 1
    assert client.post(f"/episodes/{identifier}/approve").status_code == 200


def test_mock_providers():
    from app.providers import MockRecognizer, MockSynthesizer, MockTranslator
    assert MockRecognizer().transcribe("unused")[0]["start_ms"] == 0
    assert MockTranslator().translate("你好", "") == "Xin chào"
    assert MockSynthesizer().synthesize("test", "mock").startswith(b"RIFF")
