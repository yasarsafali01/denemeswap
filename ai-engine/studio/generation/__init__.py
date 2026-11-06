from .base import Backend, GenerationError
from .passthrough import PassthroughBackend
from .wan_animate import WanAnimateBackend

BACKENDS: dict[str, type[Backend]] = {
    PassthroughBackend.name: PassthroughBackend,
    WanAnimateBackend.name: WanAnimateBackend,
}


def get_backend(name: str) -> Backend:
    if name not in BACKENDS:
        raise ValueError(f"Bilinmeyen backend: {name}. Seçenekler: {', '.join(BACKENDS)}")
    return BACKENDS[name]()


__all__ = ["Backend", "GenerationError", "BACKENDS", "get_backend"]
