#!/usr/bin/env bash
# Sets up Wan 2.2 Animate + this project on a Linux cloud GPU box (e.g. RunPod, PyTorch/CUDA image).
# Usage: bash setup_wan.sh [install_dir]
set -euo pipefail

DIR="${1:-/workspace}"
cd "$DIR"

apt-get update -y && apt-get install -y --no-install-recommends ffmpeg git-lfs

if [ ! -d Wan2.2 ]; then
  git clone https://github.com/Wan-Video/Wan2.2.git
fi
cd Wan2.2
pip install -r requirements.txt
# Animate preprocessing has its own extra requirements in the repo.
if [ -f requirements_animate.txt ]; then pip install -r requirements_animate.txt; fi

pip install "huggingface_hub[cli]"
huggingface-cli download Wan-AI/Wan2.2-Animate-14B --local-dir "$DIR/Wan2.2-Animate-14B"

cat <<EOF

Kurulum tamam. Şunları ayarlayın:
  export WAN_REPO=$DIR/Wan2.2
  export WAN_CKPT=$DIR/Wan2.2-Animate-14B
  export WAN_OFFLOAD=0   # 80 GB GPU'da offload gerekmez
EOF
