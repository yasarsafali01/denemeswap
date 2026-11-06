"""Downloads Wan 2.2 Animate (fp8) + helper models into ComfyUI/models (~31 GB).

Uses huggingface_hub (parallel Xet/chunked downloads, much faster than a single curl
connection). Files that already exist with the right size are skipped.

Usage (with ComfyUI's venv, which has huggingface_hub):
  tools/ComfyUI/.venv/Scripts/python.exe infrastructure/local-gpu/download_models.py
"""

import shutil
import sys
import tempfile
from pathlib import Path

from huggingface_hub import HfApi, hf_hub_download

ROOT = Path(__file__).resolve().parents[2]
MODELS = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "tools" / "ComfyUI" / "models"

# (repo, file in repo, destination under models/)
FILES = [
    ("Kijai/WanVideo_comfy_fp8_scaled", "Wan22Animate/Wan2_2-Animate-14B_fp8_scaled_e4m3fn_KJ_v2.safetensors",
     "diffusion_models/WanVideo/2_2/Wan2_2-Animate-14B_fp8_scaled_e4m3fn_KJ_v2.safetensors"),
    ("Kijai/WanVideo_comfy", "umt5-xxl-enc-bf16.safetensors", "text_encoders/umt5-xxl-enc-bf16.safetensors"),
    ("Kijai/WanVideo_comfy", "Wan2_1_VAE_bf16.safetensors", "vae/wanvideo/Wan2_1_VAE_bf16.safetensors"),
    ("Comfy-Org/Wan_2.1_ComfyUI_repackaged", "split_files/clip_vision/clip_vision_h.safetensors",
     "clip_vision/clip_vision_h.safetensors"),
    ("Kijai/WanVideo_comfy", "Lightx2v/lightx2v_I2V_14B_480p_cfg_step_distill_rank64_bf16.safetensors",
     "loras/WanVideo/Lightx2v/lightx2v_I2V_14B_480p_cfg_step_distill_rank64_bf16.safetensors"),
    ("Kijai/WanVideo_comfy", "LoRAs/Wan22_relight/WanAnimate_relight_lora_fp16.safetensors",
     "loras/WanVideo/WanAnimate_relight_lora_fp16.safetensors"),
    ("Wan-AI/Wan2.2-Animate-14B", "process_checkpoint/det/yolov10m.onnx", "detection/yolov10m.onnx"),
    ("JunkyByte/easy_ViTPose", "onnx/wholebody/vitpose-l-wholebody.onnx", "detection/vitpose-l-wholebody.onnx"),
]


def remote_size(api: HfApi, repo: str, filename: str) -> int:
    info = api.get_paths_info(repo, [filename])[0]
    return info.size


def main() -> int:
    api = HfApi()
    for repo, filename, dest in FILES:
        dst = MODELS / dest
        size = remote_size(api, repo, filename)
        if dst.is_file() and dst.stat().st_size == size:
            print(f"==> {dest} (zaten var, atlandı)", flush=True)
            continue
        print(f"==> {dest} ({size / 1024**3:.2f} GB)", flush=True)
        dst.parent.mkdir(parents=True, exist_ok=True)
        # Download next to the target (same drive) so the final move is instant.
        with tempfile.TemporaryDirectory(dir=MODELS, prefix=".dl_") as tmp:
            path = hf_hub_download(repo, filename, local_dir=tmp)
            if dst.exists():
                dst.unlink()  # stale partial file from an earlier run
            shutil.move(path, dst)
        if dst.stat().st_size != size:
            print(f"HATA: {dest} boyutu uyuşmuyor", flush=True)
            return 1
    print("Tüm modeller indirildi.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
