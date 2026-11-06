"""FFmpeg/ffprobe wrappers: probe, cut, normalize, concat, mux."""

import json
import shutil
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path


class FFmpegError(RuntimeError):
    pass


def _tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise FFmpegError(f"'{name}' PATH'te bulunamadı. INSTALL.md'ye bakın.")
    return path


def _run(cmd: list) -> str:
    cmd = [str(c) for c in cmd]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise FFmpegError(f"Komut başarısız: {' '.join(cmd)}\n{result.stderr[-2000:]}")
    return result.stdout


def parse_rate(rate: str | None) -> float:
    """'30000/1001' -> 29.97. Returns 0.0 for missing or '0/0'."""
    if not rate:
        return 0.0
    if "/" in rate:
        num, den = rate.split("/", 1)
        num, den = float(num), float(den)
        return num / den if den else 0.0
    return float(rate)


@dataclass
class VideoInfo:
    path: str
    duration: float
    width: int
    height: int
    fps: float
    frame_count: int
    video_codec: str
    has_audio: bool
    audio_codec: str | None

    def to_dict(self) -> dict:
        return asdict(self)


def _rotation(stream: dict) -> int:
    for side in stream.get("side_data_list", []) or []:
        if "rotation" in side:
            return int(float(side["rotation"]))
    rotate = (stream.get("tags") or {}).get("rotate")
    return int(rotate) if rotate else 0


def probe(path: str | Path) -> VideoInfo:
    out = _run([_tool("ffprobe"), "-v", "error", "-print_format", "json",
                "-show_format", "-show_streams", path])
    data = json.loads(out)
    streams = data.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    if video is None:
        raise FFmpegError(f"Video akışı bulunamadı: {path}")
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)

    fps = parse_rate(video.get("avg_frame_rate")) or parse_rate(video.get("r_frame_rate"))
    duration = float(video.get("duration") or data.get("format", {}).get("duration") or 0)

    nb = str(video.get("nb_frames") or "")
    frame_count = int(nb) if nb.isdigit() else round(duration * fps)

    width, height = int(video["width"]), int(video["height"])
    # Phone videos store portrait as landscape + rotation metadata.
    if abs(_rotation(video)) in (90, 270):
        width, height = height, width

    return VideoInfo(
        path=str(path),
        duration=duration,
        width=width,
        height=height,
        fps=fps,
        frame_count=frame_count,
        video_codec=video.get("codec_name", "unknown"),
        has_audio=audio is not None,
        audio_codec=audio.get("codec_name") if audio else None,
    )


# Near-lossless intermediate encoding so repeated cuts don't degrade quality.
_X264 = ["-c:v", "libx264", "-preset", "medium", "-crf", "12", "-pix_fmt", "yuv420p"]


def cut_segment(src: str | Path, dst: str | Path, start_frame: int, frame_count: int, fps: float) -> Path:
    """Frame-accurate cut (re-encoded, no audio). Audio is muxed back at the end."""
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    _run([_tool("ffmpeg"), "-y", "-v", "error",
          "-ss", f"{start_frame / fps:.6f}", "-i", src,
          "-frames:v", frame_count, "-an", *_X264, dst])
    return dst


def normalize(src: str | Path, dst: str | Path, width: int, height: int, fps: float) -> Path:
    """Bring a generated clip back to the source resolution/fps so segments can be concatenated."""
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    vf = (f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
          f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,fps={fps:.6f},setsar=1")
    _run([_tool("ffmpeg"), "-y", "-v", "error", "-i", src, "-an", "-vf", vf, *_X264, dst])
    return dst


def concat(clips: list[Path], dst: str | Path) -> Path:
    """Concatenate clips with identical encoding (stream copy, no re-encode)."""
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    list_file = dst.with_suffix(".concat.txt")
    lines = []
    for clip in clips:
        p = Path(clip).resolve().as_posix().replace("'", r"'\''")
        lines.append(f"file '{p}'")
    list_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    _run([_tool("ffmpeg"), "-y", "-v", "error", "-f", "concat", "-safe", "0",
          "-i", list_file, "-c", "copy", dst])
    list_file.unlink()
    return dst


def mux_audio(video: str | Path, audio_source: str | Path, dst: str | Path) -> Path:
    """Copy video stream, take audio from the original file."""
    dst = Path(dst)
    _run([_tool("ffmpeg"), "-y", "-v", "error", "-i", video, "-i", audio_source,
          "-map", "0:v:0", "-map", "1:a:0?", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
          "-shortest", "-movflags", "+faststart", dst])
    return dst


def finalize_without_audio(video: str | Path, dst: str | Path) -> Path:
    dst = Path(dst)
    _run([_tool("ffmpeg"), "-y", "-v", "error", "-i", video, "-c", "copy",
          "-movflags", "+faststart", dst])
    return dst
