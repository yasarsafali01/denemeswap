from abc import ABC, abstractmethod
from pathlib import Path


class GenerationError(RuntimeError):
    pass


class Backend(ABC):
    """Takes one short segment + reference image, writes a generated clip.

    The output may have a different resolution/fps than the input;
    the pipeline normalizes it back to the source afterwards.
    """

    name: str = ""

    def check(self) -> None:
        """Raise GenerationError if the backend can't run on this machine."""

    @abstractmethod
    def generate(self, segment: Path, reference: Path, output: Path, workdir: Path) -> Path:
        ...
