import shutil
from pathlib import Path

from .base import Backend


class PassthroughBackend(Backend):
    """Returns the segment unchanged. Used to test the full pipeline without a GPU."""

    name = "passthrough"

    def generate(self, segment: Path, reference: Path, output: Path, workdir: Path) -> Path:
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(segment, output)
        return output
