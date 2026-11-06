"""Turn the converted example workflow into the one the comfyui-local backend uses.

Changes for an 8 GB GPU on Windows:
- all 40 transformer blocks swapped to RAM, embeddings offloaded too
- sdpa attention (sageattention isn't installed), no torch.compile (no triton on Windows)
- tiled VAE encode/decode
- output = raw result only (the example renders a side-by-side comparison grid);
  audio is muxed back by our own pipeline

Usage: python tools/build_wan_workflow.py workflows/wan_animate_raw.json workflows/wan_animate_api.json
"""

import json
import sys


def prune(wf: dict, outputs: list[str]) -> dict:
    needed, stack = set(), list(outputs)
    while stack:
        nid = stack.pop()
        if nid in needed:
            continue
        needed.add(nid)
        stack += [v[0] for v in wf[nid]["inputs"].values() if isinstance(v, list) and len(v) == 2 and isinstance(v[0], str)]
    return {k: v for k, v in wf.items() if k in needed}


def build(wf: dict) -> dict:
    loader = wf["22"]["inputs"]
    loader["model"] = "WanVideo\\2_2\\Wan2_2-Animate-14B_fp8_scaled_e4m3fn_KJ_v2.safetensors"
    loader["attention_mode"] = "sdpa"
    loader.pop("compile_args", None)

    wf["51"]["inputs"].update(blocks_to_swap=40, offload_img_emb=True, offload_txt_emb=True)
    wf["27"]["inputs"]["batched_cfg"] = False
    wf["28"]["inputs"]["enable_vae_tiling"] = True
    wf["62"]["inputs"]["tiled_vae"] = True
    wf["178"]["inputs"]["yolo_model"] = "yolov10m.onnx"
    wf["65"]["inputs"]["positive_prompt"] = "a person moving naturally, high quality, detailed"

    out = wf["30"]["inputs"]
    out["images"] = ["28", 0]
    out.pop("audio", None)
    out["filename_prefix"] = "studio/result"
    return prune(wf, ["30"])


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    with open(src, encoding="utf-8") as f:
        wf = build(json.load(f))
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(wf, f, indent=2, ensure_ascii=False)
    print(f"{len(wf)} node -> {dst}")
