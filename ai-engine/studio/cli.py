"""Command line entry: python -m studio <command>"""

import argparse
import json
import sys
from pathlib import Path

from . import envcheck, video
from .generation import BACKENDS
from .scenes import detect_scenes, plan_segments

DEFAULT_WORKSPACE = Path(__file__).resolve().parents[2] / "workspace"


def _print_json(data) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False))


def cmd_check_env(args) -> int:
    report = envcheck.collect()
    _print_json(report)
    issues = envcheck.problems(report)
    for issue in issues:
        print(f"SORUN: {issue}", file=sys.stderr)
    return 1 if issues else 0


def cmd_probe(args) -> int:
    _print_json(video.probe(args.video).to_dict())
    return 0


def cmd_scenes(args) -> int:
    info = video.probe(args.video)
    scenes = detect_scenes(args.video, info.frame_count, args.threshold)
    segments = plan_segments(scenes, info.fps, args.max_segment)
    _print_json({"scenes": scenes, "segments": [s.to_dict() for s in segments]})
    return 0


def cmd_run(args) -> int:
    if not args.confirm_rights:
        print("Hata: --confirm-rights gerekli. Videonun ve referans karakterin kullanım hakkına "
              "sahip olduğunuzu ve görüntüsü kullanılan kişilerin onayı olduğunu teyit edin.", file=sys.stderr)
        return 2

    from .pipeline import run

    job = run(Path(args.video), Path(args.reference), Path(args.workspace), args.backend,
              args.max_segment, keep_audio=not args.no_audio)
    return 0 if job.manifest.get("qc", {}).get("ok") else 3


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="studio", description="AI Character Studio - video karakter dönüşümü")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("check-env", help="Donanım ve araç kontrolü").set_defaults(func=cmd_check_env)

    probe = sub.add_parser("probe", help="Video metadata")
    probe.add_argument("video")
    probe.set_defaults(func=cmd_probe)

    scenes = sub.add_parser("scenes", help="Sahne ve segment planı")
    scenes.add_argument("video")
    scenes.add_argument("--threshold", type=float, default=27.0)
    scenes.add_argument("--max-segment", type=float, default=10.0, help="Saniye")
    scenes.set_defaults(func=cmd_scenes)

    run = sub.add_parser("run", help="Karakter dönüşümünü çalıştır")
    run.add_argument("--video", required=True)
    run.add_argument("--reference", required=True, help="Hedef karakter görseli")
    run.add_argument("--backend", choices=list(BACKENDS), default="passthrough")
    run.add_argument("--max-segment", type=float, default=10.0, help="Segment başına en fazla saniye")
    run.add_argument("--workspace", default=str(DEFAULT_WORKSPACE))
    run.add_argument("--no-audio", action="store_true")
    run.add_argument("--confirm-rights", action="store_true")
    run.set_defaults(func=cmd_run)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except Exception as exc:
        print(f"Hata: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
