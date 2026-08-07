from __future__ import annotations

import secrets
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException
from fastapi.responses import FileResponse

from .config import DATA_DIR, settings


ARTIFACT_DIR = DATA_DIR / "agent_artifacts"


@dataclass(slots=True)
class Artifact:
    path: Path
    filename: str
    expires_at: float


_ARTIFACTS: dict[str, Artifact] = {}


def _cleanup() -> None:
    now = time.time()
    for token, artifact in list(_ARTIFACTS.items()):
        if artifact.expires_at > now:
            continue
        _ARTIFACTS.pop(token, None)
        try:
            artifact.path.unlink()
        except OSError:
            pass


def create_markdown_artifact(content: str, filename: str = "AI-From-Zero-学习笔记.md") -> dict | None:
    if not settings.public_base_url:
        return None
    _cleanup()
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    token = secrets.token_urlsafe(24)
    path = ARTIFACT_DIR / f"{token}.md"
    encoded = content.encode("utf-8")
    if len(encoded) > 1024 * 1024:
        encoded = encoded[: 1024 * 1024].decode("utf-8", errors="ignore").encode("utf-8")
    path.write_bytes(encoded)
    expires_at = time.time() + settings.qxd_artifact_ttl
    _ARTIFACTS[token] = Artifact(path=path, filename=filename, expires_at=expires_at)
    return {
        "fileUrl": f"{settings.public_base_url}/artifacts/{token}",
        "fileName": filename,
        "fileType": "text",
        "mimeType": "text/markdown",
        "fileSize": len(encoded),
        "expiresAt": datetime.fromtimestamp(expires_at, tz=timezone.utc).isoformat().replace("+00:00", "Z"),
    }


def artifact_response(token: str) -> FileResponse:
    _cleanup()
    artifact = _ARTIFACTS.get(token)
    if not artifact or not artifact.path.exists():
        raise HTTPException(status_code=404, detail="学习笔记不存在或已过期")
    return FileResponse(
        artifact.path,
        media_type="text/markdown; charset=utf-8",
        filename=artifact.filename,
        headers={"Cache-Control": "private, no-store"},
    )
