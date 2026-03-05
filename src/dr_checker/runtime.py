# dr_checker/runtime.py
from pathlib import Path
from typing import Optional


class Runtime:
    def __init__(self, runtime_dir: Optional[str] = None):
        self.primary_ecr_image_uri: Optional[str] = None
        self.dr_ecr_image_uri: Optional[str] = None

        if runtime_dir:
            d = Path(runtime_dir)
            self.primary_ecr_image_uri = self._read(d / "primary-ecr-image-uri")
            self.dr_ecr_image_uri = self._read(d / "dr-ecr-image-uri")

    def _read(self, path: Path) -> Optional[str]:
        if path.exists() and path.is_file():
            content = path.read_text(encoding="utf-8").strip()
            return content if content else None
        return None
