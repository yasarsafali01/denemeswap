import json
import shutil
import subprocess

import pytest
from PIL import Image

from studio import pipeline, video

pytestmark = pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg gerekli")


@pytest.fixture
def sample(tmp_path):
    """4s synthetic video with a hard cut at 2s and a sine audio track."""
    clip = tmp_path / "sample.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-v", "error",
        "-f", "lavfi", "-i", "testsrc2=size=640x360:rate=25:duration=2",
        "-f", "lavfi", "-i", "color=c=red:size=640x360:rate=25:duration=2",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=4",
        "-filter_complex", "[0:v][1:v]concat=n=2:v=1:a=0[v]",
        "-map", "[v]", "-map", "2:a", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(clip),
    ], check=True)
    ref = tmp_path / "ref.png"
    Image.new("RGB", (512, 768), "blue").save(ref)
    return clip, ref


def test_probe(sample):
    info = video.probe(sample[0])
    assert (info.width, info.height) == (640, 360)
    assert info.fps == 25
    assert info.has_audio


def test_passthrough_end_to_end(sample, tmp_path):
    clip, ref = sample
    job = pipeline.run(clip, ref, tmp_path / "ws", "passthrough", max_segment_seconds=10, log=lambda m: None)

    manifest = json.loads((job.root / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "done"
    assert len(manifest["segments"]) == 2  # the cut at 2s splits the video
    assert manifest["qc"]["ok"], manifest["qc"]["issues"]

    out = video.probe(job.path("output", "result.mp4"))
    assert out.frame_count == 100
    assert out.has_audio
