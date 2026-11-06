# Kurulum

## 1. Sistem araçları (Windows)

```powershell
winget install --id Python.Python.3.12 --scope user
winget install --id Gyan.FFmpeg
```

Kurulumdan sonra terminali yeniden açın ve kontrol edin: `ffmpeg -version`

## 2. Python ortamı

```powershell
cd ai-engine
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest            # testler
.\.venv\Scripts\python.exe -m studio check-env  # GPU ve araç kontrolü
```

## 3. (İsteğe bağlı) Yerel PyTorch: RTX 50 serisi

RTX 5060 (Blackwell) için CUDA 12.8 veya üstü PyTorch sürümü gerekir:

```powershell
.\.venv\Scripts\python.exe -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128
```

Not: Wan 2.2 Animate 14B, 8 GB VRAM'e sığmaz. Yerel GPU şimdilik ön işleme ve küçük modeller için kullanılır.

## 4. Wan 2.2 Animate (bulut GPU)

Önerilen makine: Linux + 80 GB GPU (A100/H100), en az 100 GB disk. Model ağırlıkları yaklaşık 60 GB.

```bash
# Bulut makinesinde
git clone <bu-repo> && cd <bu-repo>
bash infrastructure/cloud-gpu/setup_wan.sh /workspace
cd ai-engine && pip install -r requirements.txt
```

Model lisansını entegrasyondan önce kontrol edin: https://huggingface.co/Wan-AI/Wan2.2-Animate-14B

## 5. Ortam değişkenleri

`.env` dosyası kullanılmaz; değişkenler shell'de ayarlanır. Örnek:

```bash
WAN_REPO=/workspace/Wan2.2                 # Wan2.2 deposu
WAN_CKPT=/workspace/Wan2.2-Animate-14B     # model ağırlıkları
WAN_PYTHON=python                          # Wan'ı çalıştıracak python (varsayılan: mevcut)
WAN_RESOLUTION="1280 720"                  # üretim alanı; düşürmek VRAM ve süre kazandırır
WAN_OFFLOAD=1                              # 1: model offload (küçük GPU), 0: kapalı (80 GB GPU)
WAN_RELIGHTING=1                           # sahne ışığına uyum LoRA'sı
```

Çalıştırma:

```bash
python -m studio run --video ornek.mp4 --reference karakter.png --backend wan-animate --confirm-rights
```

## Veritabanı

Bu aşamada veritabanı yok. PostgreSQL ve Redis, Aşama 5'te (backend) eklenecek.
