"""Wan 2.2 Animate through a local ComfyUI server (WanVideoWrapper nodes).

Runs the 14B model on small GPUs: fp8 weights stay in system RAM and transformer
blocks are swapped onto the GPU one at a time (block swap). Slow but fits 8 GB VRAM.

The API workflow lives in ai-engine/workflows/wan_animate_api.json; node ids below
refer to that file.
"""

import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

import requests

from .. import video
from .base import Backend, GenerationError

ENGINE_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ENGINE_ROOT / "workflows" / "wan_animate_api.json"
DEFAULT_COMFY_ROOT = ENGINE_ROOT.parent / "tools" / "ComfyUI"

# Node ids in wan_animate_api.json
N_VIDEO, N_REF, N_WIDTH, N_HEIGHT = "63", "57", "150", "151"
N_TEXT, N_SAMPLER, N_BLOCKSWAP, N_OUTPUT = "65", "27", "51", "30"


def fit_resolution(width: int, height: int, area: int, multiple: int = 16) -> tuple[int, int]:
    """Scale to roughly `area` pixels, keep aspect ratio, round to the model's grid."""
    scale = (area / (width * height)) ** 0.5
    w = max(multiple, round(width * scale / multiple) * multiple)
    h = max(multiple, round(height * scale / multiple) * multiple)
    return w, h


class ComfyUIBackend(Backend):
    name = "comfyui-local"

    def __init__(self):
        self.url = os.environ.get("COMFY_URL", "http://127.0.0.1:8188").rstrip("/")
        self.root = Path(os.environ.get("COMFY_ROOT", DEFAULT_COMFY_ROOT))
        self.area = int(os.environ.get("WAN_AREA", 832 * 480))
        self.blocks_to_swap = int(os.environ.get("WAN_BLOCKS_TO_SWAP", 40))
        self.steps = int(os.environ.get("WAN_STEPS", 4))
        self.seed = int(os.environ.get("WAN_SEED", 42))
        self.prompt = os.environ.get("WAN_PROMPT", "a person moving naturally, high quality, detailed")
        self.client_id = uuid.uuid4().hex

    # --- server -----------------------------------------------------------------

    def _alive(self) -> bool:
        try:
            return requests.get(f"{self.url}/system_stats", timeout=3).ok
        except requests.RequestException:
            return False

    def _start_server(self) -> None:
        python = self.root / ".venv" / "Scripts" / "python.exe"
        if not python.is_file():
            python = self.root / ".venv" / "bin" / "python"
        if not python.is_file():
            raise GenerationError(f"ComfyUI bulunamadı: {self.root}. INSTALL.md > Yerel GPU.")
        log = open(self.root / "comfyui.log", "a", encoding="utf-8")
        flags = subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
        subprocess.Popen([str(python), "main.py", "--port", self.url.rsplit(":", 1)[-1]],
                         cwd=self.root, stdout=log, stderr=subprocess.STDOUT, creationflags=flags)
        # Custom node imports take a while on first start.
        for _ in range(180):
            if self._alive():
                return
            time.sleep(1)
        raise GenerationError(f"ComfyUI 3 dakikada açılmadı. Log: {self.root / 'comfyui.log'}")

    def check(self) -> None:
        if not WORKFLOW.is_file():
            raise GenerationError(f"Workflow eksik: {WORKFLOW}")
        if not self._alive():
            self._start_server()

    # --- api --------------------------------------------------------------------

    def _upload(self, path: Path) -> str:
        with path.open("rb") as fh:
            r = requests.post(f"{self.url}/upload/image",
                              files={"image": (f"{uuid.uuid4().hex[:8]}_{path.name}", fh)},
                              data={"overwrite": "true"}, timeout=120)
        r.raise_for_status()
        info = r.json()
        return f"{info['subfolder']}/{info['name']}" if info.get("subfolder") else info["name"]

    def _wait(self, prompt_id: str, log_path: Path) -> dict:
        started = time.monotonic()
        while True:
            r = requests.get(f"{self.url}/history/{prompt_id}", timeout=30)
            r.raise_for_status()
            entry = r.json().get(prompt_id)
            if entry:
                status = entry.get("status", {})
                log_path.write_text(json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")
                if status.get("status_str") == "error":
                    msgs = [m for m in status.get("messages", []) if m[0] == "execution_error"]
                    detail = msgs[-1][1].get("exception_message", "") if msgs else ""
                    raise GenerationError(f"ComfyUI hatası: {detail.strip()} (log: {self.root / 'comfyui.log'})")
                if status.get("completed"):
                    return entry["outputs"]
            if not self._alive():
                raise GenerationError("ComfyUI sunucusu iş sırasında kapandı (bellek yetmemiş olabilir).")
            if time.monotonic() - started > 6 * 3600:
                raise GenerationError("İş 6 saati aştı, iptal edildi.")
            time.sleep(5)

    def _download(self, outputs: dict, dst: Path) -> Path:
        files = outputs.get(N_OUTPUT, {}).get("gifs") or outputs.get(N_OUTPUT, {}).get("videos") or []
        if not files:
            raise GenerationError(f"Çıktı videosu bulunamadı: {list(outputs)}")
        f = files[0]
        r = requests.get(f"{self.url}/view", params={"filename": f["filename"], "subfolder": f.get("subfolder", ""),
                                                     "type": f.get("type", "output")}, timeout=300)
        r.raise_for_status()
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(r.content)
        return dst

    # --- generate ---------------------------------------------------------------

    def build_workflow(self, video_name: str, ref_name: str, width: int, height: int, prefix: str) -> dict:
        wf = json.loads(WORKFLOW.read_text(encoding="utf-8"))
        wf[N_VIDEO]["inputs"]["video"] = video_name
        wf[N_REF]["inputs"]["image"] = ref_name
        wf[N_WIDTH]["inputs"]["value"] = width
        wf[N_HEIGHT]["inputs"]["value"] = height
        wf[N_TEXT]["inputs"]["positive_prompt"] = self.prompt
        wf[N_SAMPLER]["inputs"]["steps"] = self.steps
        wf[N_SAMPLER]["inputs"]["seed"] = self.seed
        wf[N_BLOCKSWAP]["inputs"]["blocks_to_swap"] = self.blocks_to_swap
        wf[N_OUTPUT]["inputs"]["filename_prefix"] = prefix
        return wf

    def generate(self, segment: Path, reference: Path, output: Path, workdir: Path) -> Path:
        self.check()
        workdir.mkdir(parents=True, exist_ok=True)
        info = video.probe(segment)
        width, height = fit_resolution(info.width, info.height, self.area)

        wf = self.build_workflow(self._upload(segment), self._upload(reference), width, height,
                                 f"studio/{output.stem}_{uuid.uuid4().hex[:6]}")
        (workdir / "workflow.json").write_text(json.dumps(wf, indent=2, ensure_ascii=False), encoding="utf-8")

        r = requests.post(f"{self.url}/prompt", json={"prompt": wf, "client_id": self.client_id}, timeout=60)
        if not r.ok:
            raise GenerationError(f"Workflow reddedildi: {r.text[:1500]}")
        outputs = self._wait(r.json()["prompt_id"], workdir / "comfy_status.json")
        return self._download(outputs, output)
