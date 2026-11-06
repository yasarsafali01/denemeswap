"""Scene (shot) detection and segment planning. Everything is in frames to avoid rounding drift."""

import math
from dataclasses import dataclass, asdict


@dataclass
class Segment:
    index: int
    scene: int
    start_frame: int
    end_frame: int  # exclusive

    @property
    def frame_count(self) -> int:
        return self.end_frame - self.start_frame

    def to_dict(self) -> dict:
        return {**asdict(self), "frame_count": self.frame_count}


def detect_scenes(video_path: str, total_frames: int, threshold: float = 27.0) -> list[tuple[int, int]]:
    """Returns [(start_frame, end_frame_exclusive), ...]. Whole video is one scene if there are no cuts."""
    from scenedetect import ContentDetector, detect

    scenes = detect(video_path, ContentDetector(threshold=threshold))
    if not scenes:
        return [(0, total_frames)]
    return [(s.get_frames(), e.get_frames()) for s, e in scenes]


def merge_short_scenes(scenes: list[tuple[int, int]], min_frames: int) -> list[tuple[int, int]]:
    """Glue scenes shorter than min_frames onto the previous one (detector noise, flashes)."""
    merged: list[list[int]] = []
    for start, end in scenes:
        if merged and (end - start) < min_frames:
            merged[-1][1] = end
        else:
            merged.append([start, end])
    # A short first scene has nothing before it; merge it forward instead.
    if len(merged) > 1 and (merged[0][1] - merged[0][0]) < min_frames:
        merged[1][0] = merged[0][0]
        merged.pop(0)
    return [(s, e) for s, e in merged]


def plan_segments(scenes: list[tuple[int, int]], fps: float, max_seconds: float,
                  min_seconds: float = 1.0) -> list[Segment]:
    """Split scenes into equal-length chunks no longer than max_seconds."""
    min_frames = max(1, round(min_seconds * fps))
    max_frames = max(min_frames, round(max_seconds * fps))

    segments: list[Segment] = []
    for scene_idx, (start, end) in enumerate(merge_short_scenes(scenes, min_frames)):
        length = end - start
        parts = max(1, math.ceil(length / max_frames))
        step = length / parts
        for p in range(parts):
            s = start + round(p * step)
            e = start + round((p + 1) * step) if p < parts - 1 else end
            segments.append(Segment(len(segments), scene_idx, s, e))
    return segments
