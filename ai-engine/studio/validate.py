"""Input checks for the source video and the reference character image."""

from pathlib import Path

from .video import VideoInfo

VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".webm", ".avi"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}

MAX_VIDEO_BYTES = 2 * 1024**3
MAX_DURATION_S = 120
MIN_SIDE_PX = 256
MIN_REFERENCE_SIDE_PX = 512


class ValidationError(ValueError):
    pass


def validate_video_file(path: Path) -> None:
    if not path.is_file():
        raise ValidationError(f"Video bulunamadı: {path}")
    if path.suffix.lower() not in VIDEO_EXTS:
        raise ValidationError(f"Desteklenmeyen video türü: {path.suffix}")
    if path.stat().st_size > MAX_VIDEO_BYTES:
        raise ValidationError("Video 2 GB sınırını aşıyor.")


def validate_video_info(info: VideoInfo) -> list[str]:
    """Raises on hard errors, returns soft warnings."""
    if info.fps <= 0 or info.frame_count <= 0:
        raise ValidationError("Kare hızı veya kare sayısı okunamadı (bozuk video olabilir).")
    if min(info.width, info.height) < MIN_SIDE_PX:
        raise ValidationError(f"Çözünürlük çok düşük: {info.width}x{info.height}")
    if info.duration > MAX_DURATION_S:
        raise ValidationError(f"Video {MAX_DURATION_S} saniyeden uzun ({info.duration:.1f}s). PoC için kısaltın.")

    warnings = []
    if info.duration > 15:
        warnings.append("İlk testler için 5–10 saniyelik video önerilir.")
    if max(info.width, info.height) > 1280:
        warnings.append("720p üstü çözünürlük: üretim süresi ve VRAM ihtiyacı belirgin şekilde artar.")
    return warnings


def validate_reference(path: Path) -> list[str]:
    from PIL import Image

    if not path.is_file():
        raise ValidationError(f"Referans görsel bulunamadı: {path}")
    if path.suffix.lower() not in IMAGE_EXTS:
        raise ValidationError(f"Desteklenmeyen görsel türü: {path.suffix}")
    try:
        with Image.open(path) as img:
            img.verify()
        with Image.open(path) as img:
            width, height = img.size
    except Exception as exc:
        raise ValidationError(f"Görsel açılamadı: {exc}") from exc

    warnings = []
    if min(width, height) < MIN_REFERENCE_SIDE_PX:
        warnings.append(f"Referans görsel küçük ({width}x{height}); en az {MIN_REFERENCE_SIDE_PX}px önerilir.")
    if width > height:
        warnings.append("Tam karakter dönüşümü için boydan, dik (portrait) referans görsel daha iyi sonuç verir.")
    return warnings
