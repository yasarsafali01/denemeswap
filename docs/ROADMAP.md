# AI Character Studio
## Teknik Proje Yol Haritası

**Belge türü:** Teknik yol haritası  
**Ürün yaklaşımı:** Önce kurum içi / kişisel kullanım, ileride ticarileştirilebilir  
**Ana hedef:** Var olan bir videodaki seçilmiş karakteri; yüz, saç, vücut ve kıyafet görünümüyle birlikte başka bir karaktere dönüştürmek. Orijinal sahnenin hareketini, kamera perspektifini, ışığını ve mümkün olduğunca zaman içindeki tutarlılığı korumak.

---

## 1. Proje hedefi ve kapsamı

Geliştirilecek yazılım, kullanıcının video ve hedef karakter referans görsellerini yüklemesine; videodaki değiştirilecek kişiyi seçmesine; AI işleme sürecini başlatmasına ve oluşturulan videoyu inceleyip dışa aktarmasına imkân verecek.

### İlk ürün kapsamı

- Video yükleme ve temel video bilgilerini okuma.
- Hedef videodaki kişiyi tespit etme ve seçtirme.
- Hedef karakter için referans görsel(ler)i yükleme.
- Tam karakter dönüşümü: yüz, saç, vücut görünümü ve kıyafet.
- Sahne/kare analizi ve karakter takibi.
- Video işleme işlerinin kuyrukta yürütülmesi.
- Yerel GPU veya bulut GPU üzerinde işlem yapabilme.
- İşlem durumunu ve hataları arayüzde gösterme.
- Sonucu önizleme ve MP4 olarak dışa aktarma.
- Orijinal ses kanalını koruma veya ayrı ses dosyası olarak işleme.

### İlk sürümde kapsam dışında tutulacaklar

- Canlı kamera üzerinden gerçek zamanlı dönüşüm.
- Birden fazla karakteri aynı anda değiştirme.
- Mobil uygulama.
- Genel kullanıma açık, çok kiracılı SaaS ve ödeme sistemi.
- Profesyonel video kurgu yazılımı seviyesinde timeline.
- Her uzunlukta ve her çözünürlükte videoya kalite garantisi.

Bu özellikler, temel işleme hattı doğrulandıktan sonra değerlendirilecektir.

---

## 2. Donanım ve çalışma yaklaşımı

Mevcut bilgisayar bilgisi:

| Bileşen | Bildirilen özellik |
|---|---|
| GPU | NVIDIA RTX 5060 olduğu belirtilen, 8 GB VRAM |
| RAM | 64 GB |
| Çalışma yaklaşımı | Hibrit: yerel bilgisayar + gerektiğinde bulut GPU |
| Öncelik | Hızdan çok çıktı kalitesi |

> Not: Kullanıcı ekran kartını “GTX 5060” olarak ifade etti. Model adının RTX 5060 olup olmadığı `nvidia-smi` ve Windows Aygıt Yöneticisi ile doğrulanmalıdır. VRAM miktarı da aynı şekilde teyit edilecektir.

### Yerel bilgisayarın görevleri

- Uygulama geliştirme ve test.
- Video metadata okuma ve ön işleme.
- Kare çıkarma, sahne bölme ve dosya hazırlama.
- GPU belleğine sığan küçük modellerin denenmesi.
- Backend, frontend, veritabanı ve kuyruk servislerinin çalıştırılması.
- Bulut GPU'ya iş gönderme ve sonuçları alma.

### Bulut GPU'nun görevleri

- Büyük video üretim modellerinin çalıştırılması.
- VRAM gereksinimi yerel donanımı aşan işler.
- Uzun veya yüksek çözünürlüklü videolar.
- Yerel GPU belleği yetersiz kaldığında kalite testleri.

Bulut GPU sağlayıcısı ve GPU modeli, ilk benchmark sonuçlarından sonra seçilecektir. GPU saatlik ücretleri, depolama, veri aktarımı, vergi ve boşta bekleme maliyetleri ayrı hesaplanmalıdır.

---

## 3. Önerilen sistem mimarisi

Sistem, web uygulaması ve AI işleme motoru olarak ayrılacaktır.

```text
ai-character-studio/
|
|-- frontend/                 # React kullanıcı arayüzü
|
|-- backend/                  # Node.js API
|   |-- modules/
|   |   |-- videos/
|   |   |-- characters/
|   |   |-- jobs/
|   |   |-- users/
|   |   |-- storage/
|   |   `-- audit/
|   |-- queue/
|   |-- integrations/
|   `-- app.js
|
|-- ai-engine/                 # Python AI servisleri
|   |-- api/
|   |-- pipeline/
|   |-- detection/
|   |-- segmentation/
|   |-- tracking/
|   |-- generation/
|   |-- consistency/
|   |-- rendering/
|   `-- workers/
|
|-- infrastructure/
|   |-- docker/
|   |-- local-gpu/
|   |-- cloud-gpu/
|   |-- storage/
|   `-- monitoring/
|
|-- tests/
|-- docs/
`-- docker-compose.yml
```

### Teknoloji tercihleri

| Katman | Öneri | Sorumluluk |
|---|---|---|
| Frontend | React | Yükleme, karakter seçimi, iş durumu, önizleme |
| Backend | Node.js + Express | REST API, kullanıcı ve iş yönetimi |
| AI servis | Python + FastAPI | Model yükleme ve AI pipeline |
| Model altyapısı | PyTorch | Derin öğrenme modelleri |
| Video | FFmpeg | Kare çıkarma, ses ve video birleştirme |
| Görüntü | OpenCV | Görüntü/video yardımcı işlemleri |
| Kuyruk | Redis + BullMQ | Uzun süren işlerin yönetimi |
| Veritabanı | PostgreSQL | Kullanıcı, video, karakter ve iş metadata'sı |
| Dosya depolama | MinIO veya S3 uyumlu servis | Video, görsel ve ara çıktılar |
| İletişim | REST + WebSocket | API ve canlı işlem durumu |
| Paketleme | Docker | Tekrarlanabilir servis ortamı |

AI modelinin çalıştığı Python worker, Node.js API'den bağımsız tutulacaktır. Böylece AI altyapısı değişse bile uygulamanın geri kalanı yeniden yazılmak zorunda kalmaz.

---

## 4. Araştırılacak açık kaynak model ve araçlar

Aşağıdaki liste kesin entegrasyon kararı değil, teknik doğrulama listesidir. Her model için kod lisansı, model ağırlığı lisansı, ticari kullanım koşulları, kullanım kısıtları ve donanım gereksinimleri ayrı incelenmelidir.

| Model / araç | Planlanan rol | Doğrulama konusu |
|---|---|---|
| Wan 2.2 Animate | Ana karakter animasyonu/değiştirme adayı | Model ağırlığı lisansı, VRAM, kalite, çalışma yöntemi |
| SAM 2 | Kişi/nesne segmentasyonu | Video takibi, maske kararlılığı, lisans |
| Grounding DINO | Metinle hedef nesne/kişi bulma | Kişi tespit başarımı, lisans |
| OpenPose veya alternatif pose modeli | Vücut poz/iskelet çıkarımı | Poz doğruluğu ve lisans |
| InsightFace veya alternatifleri | Yüz analizi/kimlik özellikleri | Özellikle model ağırlıklarının kullanım koşulları |
| OpenCV | Görüntü işleme yardımcıları | Teknik entegrasyon |
| FFmpeg | Video işleme ve birleştirme | Codec ve dağıtım lisansı |
| ComfyUI | Prototip ve model iş akışlarını deneme | Üretim sistemine doğrudan bağımlı olmama |

### Model seçim ölçütleri

1. Tam karakter değiştirme hedefini gerçekten desteklemesi.
2. Birden fazla kare boyunca karakter kimliğini koruyabilmesi.
3. Saç, kıyafet ve vücut görünümünde tutarlı sonuç verebilmesi.
4. Orijinal hareket ve sahne kompozisyonunu koruyabilmesi.
5. Yerel/bulut GPU senaryolarında çalıştırılabilmesi.
6. Lisansının planlanan kullanım biçimine uygun olması.
7. Aynı test videolarında ölçülebilir kalite ve süre sonuçları vermesi.

---

## 5. AI video işleme pipeline'ı

Temel işleme akışı aşağıdaki sırayla tasarlanacaktır:

1. **Dosya kabulü:** Video ve referans görselleri doğrulanır; dosya türü, boyut, süre ve çözünürlük kontrol edilir.
2. **Video analizi:** FFmpeg ile metadata okunur; kare hızı, çözünürlük, ses kanalı ve süre belirlenir.
3. **Sahne bölme:** Video sahne/shot bazında parçalara ayrılır. Böylece farklı kamera açıları ve kesmeler ayrı işlenebilir.
4. **Hedef kişi tespiti:** Kullanıcının seçtiği kişi karelerde bulunur.
5. **Segmentasyon ve takip:** Kişinin maskesi ve kareler arasındaki konumu takip edilir.
6. **Referans karakter hazırlığı:** Kullanıcının sağladığı referans görseller kalite ve uygunluk açısından kontrol edilir.
7. **Hareket/poz analizi:** Gerekli durumlarda vücut pozu ve hareket bilgisi çıkarılır.
8. **Karakter üretimi/değiştirme:** Seçilen üretim modeliyle yeni karakter sahneye uyarlanır.
9. **Tutarlılık kontrolü:** Kareler arasında yüz, saç, kıyafet ve vücut görünümü değişimleri incelenir.
10. **Birleştirme ve render:** Kareler videoya dönüştürülür; ses korunur veya kullanıcı tercihine göre eklenir.
11. **Kalite kontrol:** Çıktı çözünürlüğü, süre, ses senkronu ve bozuk kareler kontrol edilir.
12. **Teslim:** Sonuç kullanıcıya önizleme ve indirme için sunulur.

Uzun videolar tek parça olarak işlenmek yerine sahne ve kısa segmentlere ayrılacaktır. Segment sınırlarında görüntü devamlılığı ayrıca test edilecektir.

---

## 6. Hibrit GPU orkestrasyonu

AI işleme servisi, işin hangi GPU'da çalıştığını uygulamanın geri kalanından gizleyecektir.

Önerilen iş parametreleri:

```json
{
  "videoId": "video-123",
  "characterId": "character-456",
  "mode": "full-replacement",
  "quality": "high",
  "gpuTarget": "auto"
}
```

GPU hedefleri:

- `local`: Yerel worker üzerinde çalıştır.
- `cloud`: Bulut worker üzerinde çalıştır.
- `auto`: Model belleği, video özellikleri ve GPU uygunluğuna göre seçim yap.

### İş yönetimi kuralları

- Her işin benzersiz kimliği ve durumu olmalıdır.
- GPU worker kapasitesi ve VRAM uygunluğu kontrol edilmelidir.
- Aynı GPU'ya kontrolsüz sayıda ağır iş gönderilmemelidir.
- Başarısız işler için sınırlı tekrar deneme ve hata kaydı bulunmalıdır.
- Buluta gönderilen dosyalar güvenli aktarılmalıdır.
- İş bitince geçici dosyalar saklama politikasına göre silinmelidir.
- Yerel GPU kullanılamazsa otomatik buluta geçiş, kullanıcı ayarlarına ve maliyet onayına bağlı olmalıdır.

---

## 7. Aşamalı geliştirme yol haritası

### Aşama 0 — Gereksinim ve donanım doğrulama

**Tahmini süre: 1–2 gün**

- [ ] `nvidia-smi` çıktısıyla GPU modelini doğrula.
- [ ] Gerçek VRAM miktarını doğrula.
- [ ] Windows/Linux ve sürücü durumunu belirle.
- [ ] Disk alanı ve kullanılabilir depolamayı kontrol et.
- [ ] Yerel geliştirme ve bulut GPU erişim yöntemini kararlaştır.
- [ ] Test için hakları bulunan kısa örnek videolar ve referans görseller belirle.

**Çıkış kriteri:** Donanım ve geliştirme ortamı gereksinimleri netleşmiş olmalı.

### Aşama 1 — AI laboratuvarı ve model PoC

**Tahmini süre: 1–2 hafta**

- [ ] Python sanal ortamını kur.
- [ ] Uyumlu PyTorch ve NVIDIA çalışma ortamını kur.
- [ ] Seçilen modelin resmi deposunu ve ağırlıklarını incele.
- [ ] Model lisansını ve kullanım koşullarını kaydet.
- [ ] Bulut GPU üzerinde ilk model çalıştırmasını yap.
- [ ] Kısa ve kontrollü bir video ile karakter değiştirme denemesi yap.
- [ ] Çıktı kalitesi, GPU belleği ve işlem süresini ölç.
- [ ] Yerel 8 GB GPU üzerinde hangi ön işleme adımlarının çalıştığını doğrula.

**Çıkış kriteri:** Referans karakterin kısa bir videoda dönüştürülebildiği, tekrarlanabilir bir PoC çıktısı.

### Aşama 2 — Video analiz ve ön işleme motoru

**Tahmini süre: 1–2 hafta**

- [ ] FFmpeg metadata okuma.
- [ ] Kare çıkarma ve tekrar video oluşturma.
- [ ] Sahne/shot bölme.
- [ ] Kişi tespitini entegre etme.
- [ ] Segmentasyon ve takip denemeleri.
- [ ] Referans görsel doğrulama.
- [ ] Ara dosya ve klasör standardı.
- [ ] Bozuk video ve desteklenmeyen codec kontrolleri.

**Çıkış kriteri:** Bir videodaki seçilmiş kişinin sahneler boyunca tespit edilip takip edilebilmesi.

### Aşama 3 — Karakter üretim servisi

**Tahmini süre: 2–3 hafta**

- [ ] Ana üretim modelini servis olarak çalıştır.
- [ ] Model giriş/çıkış sözleşmesini tanımla.
- [ ] Referans karakter hazırlığını entegre et.
- [ ] Sahne ve segment bazlı üretim yap.
- [ ] Segmentler arasında karakter görünümünü karşılaştır.
- [ ] Başarısız kare/segment kayıtlarını tut.
- [ ] Farklı ışık, açı, hareket ve kıyafet koşullarında test yap.

**Çıkış kriteri:** Aynı test setinde kabul edilebilir karakter tutarlılığı sağlayan üretim servisi.

### Aşama 4 — Video render ve kalite kontrol

**Tahmini süre: 1–2 hafta**

- [ ] Üretilen kareleri doğru sırada birleştir.
- [ ] FPS ve çözünürlük eşleşmesini kontrol et.
- [ ] Ses kanalını koru veya yeniden ekle.
- [ ] Segment birleşimlerinde atlama/titreme kontrolü yap.
- [ ] Bozuk kare ve eksik segment tespiti yap.
- [ ] MP4 çıktısını üret.
- [ ] Orijinal ve sonuç videosunu karşılaştırmalı göster.

**Çıkış kriteri:** Baştan sona işlenmiş, oynatılabilir ve ses senkronu kontrol edilmiş MP4.

### Aşama 5 — Backend ve iş kuyruğu

**Tahmini süre: 1–2 hafta**

- [ ] Node.js + Express projesini oluştur.
- [ ] PostgreSQL tablolarını ve migration yapısını kur.
- [ ] Video ve karakter kayıtlarını yönet.
- [ ] İş oluşturma ve durum sorgulama API'lerini yaz.
- [ ] Redis + BullMQ entegrasyonu yap.
- [ ] Python AI servisiyle haberleş.
- [ ] WebSocket ile işlem durumunu ilet.
- [ ] Yetkilendirme, dosya doğrulama ve hata yönetimini ekle.

**Çıkış kriteri:** API üzerinden iş oluşturulup kuyruğa alınabilmeli ve sonucu takip edilebilmeli.

### Aşama 6 — React arayüzü

**Tahmini süre: 1–2 hafta**

- [ ] Video yükleme ekranı.
- [ ] Referans karakter yükleme ekranı.
- [ ] Videodaki kişiyi seçme ekranı.
- [ ] İşlem kalitesi ve GPU tercihi.
- [ ] İşlem ilerleme ekranı.
- [ ] Hata ve yeniden deneme ekranı.
- [ ] Sonuç videosu önizleme.
- [ ] MP4 indirme.

**Çıkış kriteri:** Teknik komut kullanmadan arayüz üzerinden tam iş akışı tamamlanabilmeli.

### Aşama 7 — Hibrit GPU ve operasyon

**Tahmini süre: 1–2 hafta**

- [ ] Yerel GPU worker oluştur.
- [ ] Bulut GPU worker oluştur.
- [ ] GPU uygunluk kontrolü ekle.
- [ ] `local`, `cloud`, `auto` yönlendirmesini uygula.
- [ ] Dosya aktarımı ve sonuç senkronizasyonu yap.
- [ ] Maliyet ve işlem süresi kaydı tut.
- [ ] Worker kesintisi ve yeniden başlatma senaryolarını test et.

**Çıkış kriteri:** Aynı iş sözleşmesiyle yerel veya bulut GPU üzerinde işlem yapılabilmeli.

### Aşama 8 — Kalite, güvenlik ve kararlılık

**Tahmini süre: 2–3 hafta ve sürekli iyileştirme**

- [ ] Farklı video türleri için test veri seti oluştur.
- [ ] Karakter kimliği tutarlılığını ölç.
- [ ] Yüz, saç ve kıyafet bozulmalarını incele.
- [ ] Hızlı hareket ve örtüşme senaryolarını test et.
- [ ] Uzun video ve bellek sınırlarını test et.
- [ ] Kullanıcı dosyalarını özel erişimle sakla.
- [ ] Silme ve saklama politikası uygula.
- [ ] Yetkisiz/izinsiz gerçek kişi taklidi ve mahrem içerik üretimine karşı kullanım kontrolleri ekle.
- [ ] Loglarda hassas görüntü veya kişisel veri tutma.
- [ ] Model ve bağımlılık sürümlerini sabitle.

**Çıkış kriteri:** Tekrarlanabilir kalite testleri, kontrollü hata yönetimi ve güvenli dosya akışı.

---

## 8. Zaman planı

Tek geliştirici için, AI model araştırması ve donanım kaynaklı belirsizlikler dahil yaklaşık plan:

| İş paketi | Tahmini süre |
|---|---:|
| Donanım ve ortam doğrulama | 1–2 gün |
| AI model PoC | 1–2 hafta |
| Video ön işleme | 1–2 hafta |
| Karakter üretim servisi | 2–3 hafta |
| Render ve kalite kontrol | 1–2 hafta |
| Backend ve kuyruk | 1–2 hafta |
| React arayüzü | 1–2 hafta |
| Hibrit GPU | 1–2 hafta |
| Güvenlik ve kalite | 2–3 hafta |

**Genel tahmin: yaklaşık 10–16 hafta.** Bu bir planlama tahminidir; model entegrasyonu, kalite hedefi ve GPU erişimi süreyi değiştirebilir. Tam karakter değiştirme, basit yüz değiştirmeden belirgin biçimde daha zordur.

---

## 9. İlk test senaryosu ve kabul ölçütleri

İlk testte kapsamı küçük tutacağız:

- 5–10 saniyelik, tek kişinin bulunduğu bir video.
- Mümkünse tek sahne ve belirgin karakter görünümü.
- Hedef karakter için yüksek kaliteli, uygun referans görsel.
- Önce 720p veya daha düşük çözünürlükte teknik doğrulama.
- Sonrasında daha yüksek çözünürlük ve zor sahneler.

Ölçülecek kriterler:

| Kriter | Kontrol |
|---|---|
| Karakter kimliği | Kareler boyunca hedef karaktere benziyor mu? |
| Görünüm | Saç, yüz, vücut ve kıyafet korunuyor mu? |
| Hareket | Orijinal beden hareketi ve poz korunuyor mu? |
| Sahne uyumu | Işık, gölge ve perspektif doğal mı? |
| Zamansal tutarlılık | Kareler arasında titreme/kimlik kayması var mı? |
| Video çıktısı | FPS, süre, çözünürlük ve ses doğru mu? |
| Kaynak tüketimi | VRAM, RAM, GPU süresi ve depolama ne kadar? |

İlk PoC için kalite hedefi, kusursuz sinema çıktısı değil; aynı koşullarda tekrar çalıştırılabilen ve değerlendirilebilen bir sonuç elde etmektir.

---

## 10. Maliyet planı

Başlangıçta pahalı GPU satın alımı zorunlu tutulmayacaktır.

### İlk aşama

- Mevcut 8 GB GPU: geliştirme, ön işleme ve küçük testler.
- 64 GB RAM: yerel servisler ve CPU offload denemeleri.
- Bulut GPU: büyük model PoC ve kalite testleri.
- Depolama: test videoları ve ara çıktılar için yeterli NVMe alanı.

### Maliyet kalemleri

1. Bulut GPU çalışma süresi.
2. Model ve ara çıktı depolaması.
3. Bulut veri aktarımı.
4. Yerel disk ve yedekleme.
5. Gerekirse GPU donanımı.
6. Elektrik ve bakım.

Gerçek maliyet, önce 5–10 saniyelik standart test videosunda ölçüm yapılarak hesaplanacaktır. Video başına maliyet; model, çözünürlük, kare hızı, segment uzunluğu ve GPU'ya göre değişecektir. Bu nedenle doğrulanmamış sabit bir “video başı maliyet” belirlenmeyecektir.

---

## 11. Riskler ve karar noktaları

| Risk | Yaklaşım |
|---|---|
| Model 8 GB VRAM'e sığmıyor | Büyük modeli bulutta çalıştır |
| Karakter kareler arasında değişiyor | Segment/sahne bazlı üretim ve tutarlılık testleri |
| Kıyafet veya vücut bozuluyor | Referans hazırlığı ve model/pipeline karşılaştırması |
| Uzun videolar başarısız oluyor | Kısa segmentler ve checkpoint |
| Model lisansı uygun değil | Entegrasyondan önce lisans onayı |
| Bulut maliyeti artıyor | İş süresi, GPU tipi ve depolama ölçümü |
| GPU worker çöküyor | Kuyruk, retry ve iş checkpoint'i |
| Hassas video sızıyor | Özel depolama, erişim kontrolü, silme politikası |

### Karar kapıları

- **Kapı 1:** Ana model, kısa testte hedeflenen dönüşümü yapabiliyor mu?
- **Kapı 2:** Aynı karakter birkaç sahnede yeterince tutarlı mı?
- **Kapı 3:** İşleme süresi ve GPU maliyeti kabul edilebilir mi?
- **Kapı 4:** Yerel ve bulut worker aynı API sözleşmesiyle çalışabiliyor mu?
- **Kapı 5:** Kullanıcı arayüzü üzerinden baştan sona işlem tamamlanabiliyor mu?

Bir karar kapısı geçilmeden sonraki aşamaya büyük yatırım yapılmayacaktır.

---

## 12. İlk uygulanacak adımlar

Başlangıç sıramız:

1. Windows ve NVIDIA sürücü/GPU bilgisini doğrula (`nvidia-smi`).
2. Python, Git, FFmpeg ve Docker durumunu kontrol et.
3. Bulut GPU üzerinde uygun bir çalışma ortamı aç.
4. Wan 2.2 Animate resmi deposunu ve lisansını incele.
5. Modeli indirip örnek inference çalıştır.
6. Hakları bulunan kısa test videosu ve referans görseliyle ilk karakter değiştirme çıktısını üret.
7. Çıktının kalitesini, VRAM tüketimini, işlem süresini ve maliyetini kaydet.
8. PoC başarılı olursa AI pipeline'ını modüler servis haline getir.

**İlk geliştirme hedefi:** React veya Node.js ekranları değil; komut satırından çalışan, bir video ve referans karakter alıp yeni bir video üreten güvenilir AI prototipidir.

---

## 13. Kaynaklar

- Wan 2.2 resmi deposu: https://github.com/Wan-Video/Wan2.2
- SAM 2 resmi deposu: https://github.com/facebookresearch/sam2
- Grounding DINO resmi deposu: https://github.com/IDEA-Research/GroundingDINO
- PyTorch: https://pytorch.org/
- FFmpeg: https://ffmpeg.org/
- OpenCV: https://opencv.org/
- FastAPI: https://fastapi.tiangolo.com/
- BullMQ: https://docs.bullmq.io/
- RunPod GPU seçenekleri: https://www.runpod.io/gpu-models

> Kaynakların ve model lisanslarının durumu geliştirme başlangıcında yeniden doğrulanmalıdır. Bu doküman teknik planlama belgesidir; belirli model performansı, lisans uygunluğu veya donanımda çalışma garantisi vermez.
