from studio.scenes import merge_short_scenes, plan_segments
from studio.video import parse_rate


def test_parse_rate():
    assert abs(parse_rate("30000/1001") - 29.97) < 0.01
    assert parse_rate("25/1") == 25
    assert parse_rate("0/0") == 0
    assert parse_rate(None) == 0


def test_merge_short_scenes():
    assert merge_short_scenes([(0, 100), (100, 105), (105, 200)], 24) == [(0, 105), (105, 200)]
    assert merge_short_scenes([(0, 5), (5, 200)], 24) == [(0, 200)]


def test_plan_segments_covers_every_frame():
    scenes = [(0, 750), (750, 800)]  # 30s + 2s at 25fps
    segs = plan_segments(scenes, fps=25, max_seconds=10)

    assert segs[0].start_frame == 0
    assert segs[-1].end_frame == 800
    for a, b in zip(segs, segs[1:]):
        assert a.end_frame == b.start_frame
    assert all(s.frame_count <= 250 for s in segs)
    assert [s.scene for s in segs] == [0, 0, 0, 1]
