"""Wan 2.2 Animate (replacement mode) via the official repo's scripts.

The model is not imported directly: we call the repo's own preprocess + generate
scripts as subprocesses. That keeps its heavy, fast-moving dependencies isolated
from this package and lets the same code run on a cloud GPU box.

Command flags follow the Wan2.2 README (animate-14B, --replace_flag).
Re-check them against the repo version you clone during the PoC.
"""

import os
import subprocess
import sys
from pathlib import Path

from .base import Backend, GenerationError


class WanAnimateBackend(Backend):
    name = "wan-animate"

    def __init__(self):
        self.repo = Path(os.environ.get("WAN_REPO", "")).expanduser()
        self.ckpt = Path(os.environ.get("WAN_CKPT", "")).expanduser()
        self.python = os.environ.get("WAN_PYTHON", sys.executable)
        # 1280x720 area is the model's native setting; lower it to save VRAM/time.
        self.resolution = os.environ.get("WAN_RESOLUTION", "1280 720").split()
        # Model offload lets it run on smaller GPUs at the cost of speed.
        self.offload = os.environ.get("WAN_OFFLOAD", "1") == "1"
        self.relighting = os.environ.get("WAN_RELIGHTING", "1") == "1"

    def check(self) -> None:
        if not self.repo or not (self.repo / "generate.py").is_file():
            raise GenerationError("WAN_REPO ayarlı değil veya Wan2.2 deposu bulunamadı. INSTALL.md > Wan 2.2 Animate.")
        if not self.ckpt or not (self.ckpt / "process_checkpoint").is_dir():
            raise GenerationError("WAN_CKPT ayarlı değil veya Wan2.2-Animate-14B ağırlıkları eksik.")

    def _run(self, cmd: list, log: Path) -> None:
        cmd = [str(c) for c in cmd]
        with log.open("w", encoding="utf-8") as fh:
            fh.write(" ".join(cmd) + "\n\n")
            fh.flush()
            proc = subprocess.run(cmd, cwd=self.repo, stdout=fh, stderr=subprocess.STDOUT)
        if proc.returncode != 0:
            tail = log.read_text(encoding="utf-8", errors="replace")[-1500:]
            raise GenerationError(f"Wan komutu başarısız (log: {log}):\n{tail}")

    def generate(self, segment: Path, reference: Path, output: Path, workdir: Path) -> Path:
        self.check()
        prep_dir = workdir / "preprocess"
        prep_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: pose, face, background and person mask extraction.
        self._run([
            self.python, "wan/modules/animate/preprocess/preprocess_data.py",
            "--ckpt_path", self.ckpt / "process_checkpoint",
            "--video_path", segment.resolve(),
            "--refer_path", reference.resolve(),
            "--save_path", prep_dir.resolve(),
            "--resolution_area", *self.resolution,
            "--iterations", "3", "--k", "7", "--w_len", "1", "--h_len", "1",
            "--replace_flag",
        ], workdir / "preprocess.log")

        # Step 2: generate the replaced character.
        cmd = [
            self.python, "generate.py",
            "--task", "animate-14B",
            "--ckpt_dir", self.ckpt,
            "--src_root_path", prep_dir.resolve(),
            "--refert_num", "1",
            "--replace_flag",
            "--save_file", output.resolve(),
        ]
        if self.relighting:
            cmd.append("--use_relighting_lora")
        if self.offload:
            cmd += ["--offload_model", "True", "--convert_model_dtype"]
        output.parent.mkdir(parents=True, exist_ok=True)
        self._run(cmd, workdir / "generate.log")

        if not output.is_file():
            raise GenerationError(f"Wan çıktı dosyası oluşmadı: {output}")
        return output
