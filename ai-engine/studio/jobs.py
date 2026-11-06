"""Job workspace: one folder per run with a manifest.json that records every step."""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Job:
    def __init__(self, root: Path, manifest: dict):
        self.root = root
        self.manifest = manifest

    @classmethod
    def create(cls, workspace: Path, params: dict) -> "Job":
        job_id = datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]
        root = workspace / "jobs" / job_id
        for sub in ("input", "segments", "generated", "normalized", "output", "work"):
            (root / sub).mkdir(parents=True, exist_ok=True)
        job = cls(root, {
            "id": job_id,
            "status": "created",
            "created_at": _now(),
            "params": params,
            "steps": [],
            "warnings": [],
        })
        job.save()
        return job

    @property
    def id(self) -> str:
        return self.manifest["id"]

    def path(self, *parts: str) -> Path:
        return self.root.joinpath(*parts)

    def save(self) -> None:
        self.manifest["updated_at"] = _now()
        tmp = self.root / "manifest.json.tmp"
        tmp.write_text(json.dumps(self.manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.root / "manifest.json")

    def set(self, key: str, value) -> None:
        self.manifest[key] = value
        self.save()

    def warn(self, message: str) -> None:
        self.manifest["warnings"].append(message)
        self.save()

    def step(self, name: str, **data) -> None:
        self.manifest["steps"].append({"name": name, "at": _now(), **data})
        self.manifest["status"] = name
        self.save()
