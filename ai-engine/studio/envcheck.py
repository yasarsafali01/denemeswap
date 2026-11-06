"""Phase 0 environment check: tools, GPU, torch."""

import platform
import shutil
import subprocess
import sys


def collect() -> dict:
    report = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "ffmpeg": shutil.which("ffmpeg"),
        "ffprobe": shutil.which("ffprobe"),
        "gpu": None,
        "torch": None,
    }

    if shutil.which("nvidia-smi"):
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
            capture_output=True, text=True,
        ).stdout.strip()
        report["gpu"] = out or None

    try:
        import torch

        report["torch"] = {
            "version": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "cuda_version": torch.version.cuda,
            "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        }
    except ImportError:
        report["torch"] = "kurulu değil (sadece passthrough/ön işleme için gerekmez)"
    return report


def problems(report: dict) -> list[str]:
    issues = []
    if not report["ffmpeg"] or not report["ffprobe"]:
        issues.append("FFmpeg/ffprobe PATH'te değil.")
    if not report["gpu"]:
        issues.append("NVIDIA GPU bulunamadı (nvidia-smi yok).")
    return issues
