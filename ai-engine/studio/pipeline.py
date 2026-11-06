"""End-to-end run: validate -> analyze -> split -> generate -> normalize -> concat -> audio -> QC."""

import shutil
import time
from pathlib import Path
from typing import Callable

from . import video
from .generation import get_backend
from .jobs import Job
from .scenes import detect_scenes, plan_segments
from .validate import validate_reference, validate_video_file, validate_video_info

Log = Callable[[str], None]


def run(video_path: Path, reference_path: Path, workspace: Path, backend_name: str = "passthrough",
        max_segment_seconds: float = 10.0, keep_audio: bool = True, log: Log = print) -> Job:
    video_path, reference_path = Path(video_path), Path(reference_path)

    # Fail fast before creating a job folder.
    validate_video_file(video_path)
    ref_warnings = validate_reference(reference_path)
    backend = get_backend(backend_name)
    backend.check()

    job = Job.create(workspace, {
        "video": str(video_path), "reference": str(reference_path), "backend": backend_name,
        "max_segment_seconds": max_segment_seconds, "keep_audio": keep_audio,
    })
    log(f"İş oluşturuldu: {job.id}  ({job.root})")
    try:
        _run(job, video_path, reference_path, backend, max_segment_seconds, keep_audio, ref_warnings, log)
    except Exception as exc:
        job.manifest["error"] = f"{type(exc).__name__}: {exc}"
        job.step("failed")
        raise
    return job


def _run(job, video_path, reference_path, backend, max_segment_seconds, keep_audio, ref_warnings, log):
    src = job.path("input", "source" + video_path.suffix.lower())
    ref = job.path("input", "reference" + reference_path.suffix.lower())
    shutil.copyfile(video_path, src)
    shutil.copyfile(reference_path, ref)

    info = video.probe(src)
    for w in ref_warnings + validate_video_info(info):
        log(f"Uyarı: {w}")
        job.warn(w)
    job.set("source_info", info.to_dict())
    job.step("analyzed")
    log(f"Video: {info.width}x{info.height} @ {info.fps:.3f} fps, {info.duration:.2f}s, "
        f"{info.frame_count} kare, ses: {'var' if info.has_audio else 'yok'}")

    scenes = detect_scenes(str(src), info.frame_count)
    segments = plan_segments(scenes, info.fps, max_segment_seconds)
    job.set("segments", [s.to_dict() for s in segments])
    job.step("segmented", scenes=len(scenes), segments=len(segments))
    log(f"{len(scenes)} sahne, {len(segments)} segment")

    normalized = []
    for seg in segments:
        tag = f"seg_{seg.index:03d}"
        seg_file = video.cut_segment(src, job.path("segments", f"{tag}.mp4"),
                                     seg.start_frame, seg.frame_count, info.fps)
        log(f"[{seg.index + 1}/{len(segments)}] üretiliyor ({seg.frame_count} kare)...")
        started = time.monotonic()
        gen_file = backend.generate(seg_file, ref, job.path("generated", f"{tag}.mp4"),
                                    job.path("work", tag))
        elapsed = round(time.monotonic() - started, 1)
        normalized.append(video.normalize(gen_file, job.path("normalized", f"{tag}.mp4"),
                                          info.width, info.height, info.fps))
        job.step("segment_generated", segment=seg.index, seconds=elapsed)

    joined = video.concat(normalized, job.path("work", "joined.mp4"))
    result = job.path("output", "result.mp4")
    if keep_audio and info.has_audio:
        video.mux_audio(joined, src, result)
    else:
        video.finalize_without_audio(joined, result)
    job.step("rendered")

    qc = quality_check(info, video.probe(result), keep_audio)
    job.set("qc", qc)
    for issue in qc["issues"]:
        log(f"QC: {issue}")
        job.warn(issue)
    job.step("done")
    log(f"Tamamlandı: {result}")


def quality_check(src: video.VideoInfo, out: video.VideoInfo, keep_audio: bool) -> dict:
    issues = []
    if (out.width, out.height) != (src.width, src.height):
        issues.append(f"Çözünürlük farklı: {out.width}x{out.height} (kaynak {src.width}x{src.height})")
    if abs(out.fps - src.fps) > 0.01:
        issues.append(f"FPS farklı: {out.fps:.3f} (kaynak {src.fps:.3f})")
    # More than ~2 frames of drift means the generator dropped or added frames.
    if abs(out.duration - src.duration) > 2 / src.fps + 0.05:
        issues.append(f"Süre farklı: {out.duration:.2f}s (kaynak {src.duration:.2f}s)")
    if keep_audio and src.has_audio and not out.has_audio:
        issues.append("Ses kanalı çıktıda yok.")
    return {"ok": not issues, "issues": issues, "output": out.to_dict()}
