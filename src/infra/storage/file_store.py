"""Local file storage for uploaded source documents."""

from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import UploadFile

from src.core.config import get_settings


class FileStore:
    """Persists uploaded files to the configured local directory."""

    def __init__(self, base_dir: str | None = None) -> None:
        self.base_dir = Path(base_dir or get_settings().upload_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def save(self, document_id: str, upload: UploadFile) -> Path:
        destination = self.base_dir / f"{document_id}_{upload.filename}"
        with destination.open("wb") as target:
            shutil.copyfileobj(upload.file, target)
        return destination
