# AI Character Studio

Videodaki seçilen kişiyi, referans görseli verilen başka bir karaktere dönüştürür (yüz, saç, vücut, kıyafet). Orijinal hareket, kamera açısı, ışık ve ses korunur.

> **Durum:** Aşama 1–2. Komut satırından çalışan AI işleme hattı hazır. Backend ve arayüz sonraki aşamalarda gelecek. Tüm plan: [docs/ROADMAP.md](docs/ROADMAP.md)

## Mimari

```
                 ┌──────────────┐   REST/WS   ┌──────────────┐  kuyruk  ┌──────────────────────┐
   (planlı)      │ React (web)  │ ──────────▶ │ Node.js API  │ ───────▶ │ Python AI worker     │
                 └──────────────┘             │ Postgres     │  Redis   │ (yerel GPU / bulut)  │
                                              └──────────────┘          └──────────┬───────────┘
                                                                                   │
   (hazır)  ai-engine pipeline ────────────────────────────────────────────────────┘
     1. Doğrulama        video + referans görsel kontrolü
     2. Analiz           ffprobe: çözünürlük, fps, kare sayısı, ses
     3. Sahne bölme      PySceneDetect → sahneler → ≤10 sn segmentler (kare bazlı)
     4. Üretim           backend: passthrough (test) | wan-animate (Wan 2.2 Animate)
     5. Normalize        üretilen klipleri kaynak çözünürlük/fps'e geri getir
     6. Birleştirme      segmentleri birleştir, orijinal sesi ekle
     7. Kalite kontrol   çözünürlük, fps, süre, ses karşılaştırması
```

Her çalıştırma `workspace/jobs/<iş-id>/` altında ayrı bir klasör ve `manifest.json` (adımlar, süreler, uyarılar, QC sonucu) oluşturur.

Üretim backend'leri ortak bir arayüzü uygular. Wan 2.2, kendi deposundaki script'ler üzerinden alt süreç (subprocess) olarak çağrılır. Böylece ağır bağımlılıkları bu paketten ayrı kalır ve aynı kod yerelde de bulut GPU'da da çalışır.

## Klasör yapısı

```
ai-engine/
  studio/
    cli.py            komut satırı (check-env, probe, scenes, run)
    pipeline.py       uçtan uca akış + kalite kontrol
    video.py          ffmpeg/ffprobe sarmalayıcıları
    scenes.py         sahne tespiti ve segment planı
    validate.py       girdi doğrulama
    jobs.py           iş klasörü ve manifest
    envcheck.py       donanım/ortam kontrolü
    generation/       üretim backend'leri (passthrough, wan_animate)
  tests/
infrastructure/
  cloud-gpu/setup_wan.sh   bulut GPU'ya Wan 2.2 Animate kurulumu
docs/ROADMAP.md            teknik yol haritası
```

## Teknolojiler

Python 3.12, FFmpeg, PySceneDetect, OpenCV, Pillow, pytest · Model: Wan 2.2 Animate (14B) · Planlı: React, Node.js + Express, PostgreSQL, Redis + BullMQ, MinIO, Docker

## Hızlı başlangıç

```powershell
cd ai-engine
.\.venv\Scripts\python.exe -m studio run --video ornek.mp4 --reference karakter.png --confirm-rights
```

Varsayılan backend `passthrough`. GPU olmadan hattın tamamını test eder. Gerçek karakter dönüşümü için `--backend wan-animate` kullanın (bulut GPU gerekir).

Kurulum, ortam değişkenleri ve bulut GPU adımları: **[INSTALL.md](INSTALL.md)**

## Kullanım kuralı

Yalnızca kullanım hakkınız olan videoları ve görüntüsü kullanılan kişilerin onay verdiği içerikleri işleyin. `run` komutu bu yüzden `--confirm-rights` ister.
