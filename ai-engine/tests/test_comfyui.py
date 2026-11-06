from studio.generation.comfyui import (N_BLOCKSWAP, N_HEIGHT, N_OUTPUT, N_REF, N_VIDEO, N_WIDTH,
                                       ComfyUIBackend, fit_resolution)


def test_fit_resolution_keeps_aspect_and_grid():
    assert fit_resolution(1280, 720, 832 * 480) == (848, 480)
    w, h = fit_resolution(1080, 1920, 832 * 480)
    assert w % 16 == 0 and h % 16 == 0 and h > w


def test_build_workflow_patches_inputs():
    wf = ComfyUIBackend().build_workflow("v.mp4", "r.png", 848, 480, "studio/x")
    assert wf[N_VIDEO]["inputs"]["video"] == "v.mp4"
    assert wf[N_REF]["inputs"]["image"] == "r.png"
    assert wf[N_WIDTH]["inputs"]["value"] == 848
    assert wf[N_HEIGHT]["inputs"]["value"] == 480
    assert wf[N_BLOCKSWAP]["inputs"]["blocks_to_swap"] == 40
    assert wf[N_OUTPUT]["inputs"]["images"] == ["28", 0]  # raw result, not the comparison grid
    assert "audio" not in wf[N_OUTPUT]["inputs"]
    # Every link must point at a node that exists in the graph.
    for node in wf.values():
        for v in node["inputs"].values():
            if isinstance(v, list) and len(v) == 2 and isinstance(v[0], str):
                assert v[0] in wf
