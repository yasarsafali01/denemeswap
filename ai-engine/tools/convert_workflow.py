"""Convert a ComfyUI UI-format workflow (.json saved from the editor) to API format.

Needs the running server's /object_info to map widget values to input names.
Resolves frontend-only nodes (SetNode/GetNode, Reroute, notes) and keeps only
the ancestors of the chosen output nodes.

Usage:
  python tools/convert_workflow.py UI.json OUT.json --server http://127.0.0.1:8188 --keep 30
"""

import argparse
import json
import urllib.request

VIRTUAL = {"Note", "MarkdownNote", "SetNode", "GetNode", "Reroute", "PrimitiveNode"}
# Frontend adds an extra "control_after_generate" widget value after these.
SEED_NAMES = {"seed", "noise_seed"}


def _widget_inputs(info: dict) -> list[tuple[str, dict]]:
    """Ordered (name, options) of inputs that are shown as widgets."""
    out = []
    for section in ("required", "optional"):
        for name, spec in (info["input"].get(section) or {}).items():
            kind = spec[0]
            opts = spec[1] if len(spec) > 1 and isinstance(spec[1], dict) else {}
            is_widget = isinstance(kind, list) or kind in ("INT", "FLOAT", "STRING", "BOOLEAN", "COMBO")
            if opts.get("forceInput") or opts.get("rawLink"):
                is_widget = False
            if is_widget:
                out.append((name, opts))
    return out


def convert(ui: dict, object_info: dict, keep: list[int]) -> dict:
    nodes = {n["id"]: n for n in ui["nodes"]}
    links = {l[0]: l for l in ui["links"]}  # id -> [id, src, src_slot, dst, dst_slot, type]

    setters = {}
    for n in ui["nodes"]:
        if n["type"] == "SetNode":
            setters[n["widgets_values"][0]] = n

    def resolve(src: int, slot: int) -> tuple[int, int] | None:
        """Follow virtual nodes back to the real producing node."""
        node = nodes[src]
        if node.get("mode") in (2, 4):  # muted/bypassed: treat as missing
            return None
        if node["type"] == "GetNode":
            node = setters[node["widgets_values"][0]]
        if node["type"] in ("SetNode", "Reroute"):
            link_id = node["inputs"][0].get("link")
            if link_id is None:
                return None
            l = links[link_id]
            return resolve(l[1], l[2])
        return (src, slot)

    api = {}
    for n in ui["nodes"]:
        if n["type"] in VIRTUAL or n.get("mode") in (2, 4):
            continue
        info = object_info.get(n["type"])
        if info is None:
            raise KeyError(f"Sunucuda node tipi yok: {n['type']} (eklenti kurulu mu?)")

        inputs = {}
        values = n.get("widgets_values")
        if isinstance(values, dict):
            for name, _ in _widget_inputs(info):
                if name in values:
                    inputs[name] = values[name]
        elif isinstance(values, list):
            i = 0
            for name, opts in _widget_inputs(info):
                if i >= len(values):
                    break
                inputs[name] = values[i]
                i += 1
                if name in SEED_NAMES or opts.get("control_after_generate"):
                    i += 1

        for inp in n.get("inputs", []):
            if inp.get("link") is None:
                continue
            l = links[inp["link"]]
            src = resolve(l[1], l[2])
            if src is not None:
                inputs[inp["name"]] = [str(src[0]), src[1]]
            else:
                inputs.pop(inp["name"], None)

        api[str(n["id"])] = {"class_type": n["type"], "inputs": inputs, "_meta": {"title": n.get("title") or n["type"]}}

    # Keep only what the chosen outputs depend on.
    needed, stack = set(), [str(k) for k in keep]
    while stack:
        nid = stack.pop()
        if nid in needed:
            continue
        needed.add(nid)
        for v in api[nid]["inputs"].values():
            if isinstance(v, list) and len(v) == 2 and isinstance(v[0], str):
                stack.append(v[0])
    return {k: v for k, v in api.items() if k in needed}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("ui")
    p.add_argument("out")
    p.add_argument("--server", default="http://127.0.0.1:8188")
    p.add_argument("--keep", type=int, nargs="+", required=True, help="Output node ids")
    args = p.parse_args()

    with urllib.request.urlopen(f"{args.server}/object_info") as r:
        object_info = json.load(r)
    with open(args.ui, encoding="utf-8") as f:
        ui = json.load(f)
    api = convert(ui, object_info, args.keep)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(api, f, indent=2, ensure_ascii=False)
    print(f"{len(api)} node yazıldı -> {args.out}")


if __name__ == "__main__":
    main()
