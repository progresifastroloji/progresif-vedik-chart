# MİMARİ DURUM VE KARARLAR — 2026-07-29

> Bu dosya `CLAUDE.md`'yi **tamamlar, değiştirmez**. CLAUDE.md proje
> çalışma kurallarını tanımlar; bu dosya PWA/uygulama dönüşümü için
> yapılan durum tespitini ve mimari kararları tutar.
>
> Kaynak: Claude (Opus 5) + Codex denetim raporu (2026-07-29 17:11-17:18)
> Codex raporu canlı endpoint'lerle doğrulandı, dosya değiştirilmedi.

---

## 0. ACİL — HENÜZ YAPILMADI

### 0.1 Git yedeği yok (KRİTİK)

Repo geçmişinde **tek commit** var:

```
2026-04-12 | feat: Vedik astroloji harita hesaplayıcı web uygulaması
```

Nisan'dan bugüne yapılan **hiçbir iş commit edilmemiş**:
Shadbala, Ashtakavarga, yoga motoru, transit entegrasyonu, 13 paket,
rektifikasyon servisi, beta endpoint'leri, çapraz varga, hız yaması.

Çalışma ağacı "yoğun biçimde değişmiş/untracked" durumda.
`app.py.yedek-*` dosyaları tek dosyanın anlık kopyaları — klasör
kaybı senaryosunu karşılamıyor.

**Yapılacak:**

```bash
cd /Users/leventkalayci/Documents/progresifastrolog/progresif-vedik-chart
git add -A
git commit -m "checkpoint: engine 0.3.0 - yoga motoru, shadbala, ashtakavarga, transit, 13 paket"
git log --oneline
```

Sonra: GitHub private repo (uzak yedek). Henüz konuşulmadı.

**Kural: app.py'de değişiklik yapan hiçbir işe bu commit atılmadan
başlanmayacak.**

---

## 1. GERÇEK DURUM TESPİTİ

### 1.1 API v2 kodlanmış ve tasarımın ötesinde

`API-v2-Tasarim.md` (2026-05-15, vault içinde) sadece tasarım değil —
**uygulanmış**. Vault çıktılarında `api_version: "v2"`,
`engine_version: "0.3.0"`, `source: "api_v2_vault_save"`.

`/api/v2/chart/full` üst düzey anahtarları (30+):

```
analysis_modules, analysis_profile, angles, ashtakavarga, aspects,
avasthas, bhava_bala, bhava_chalit, birth, compound_friendship,
copy_packages, dashas, data_quality, decision_engine, doshas, houses,
jaimini, kp, lagna, lordships, meta, missing, panchanga, planets,
rectification, sensitive_points, shadbala, special_lagnas,
temporary_friendship, topic_packets, transits, vargas, varshaphala,
vimshopaka_bala, yogas
```

`life_period_analysis` option ile ayrıca eklenebilir.

Tasarımın Faz 1+2+3+4'ünün büyük kısmı tamam. `kp` (Krishnamurti) ve
`decision_engine` tasarımda bile yoktu.

**Sonuç: CLAUDE.md bu sistemin ne kadar ilerlediğini eksik anlatıyor.**

### 1.2 Route haritası

**app.py (port 5000):**

| Yol | Metod | Fonksiyon |
|---|---|---|
| `/` | GET | index |
| `/beta` | GET | beta_index |
| `/api/calculate` | POST | api_calculate |
| `/api/v2/chart/full` | POST | api_v2_chart_full |
| `/api/v2/chart/expert-copy` | POST | api_v2_chart_expert_copy |
| `/vedic/life-period-analysis` | GET | vedic_life_period_analysis |
| `/api/v2/rectification/analyze` | POST | api_v2_rectification_analyze |
| `/api/v2/rectification/report` | POST | api_v2_rectification_report |
| `/api/v2/rectification/save` | POST | api_v2_rectification_save |
| `/api/v2/transits/pack` | POST | api_v2_transits_pack |
| `/api/v2/vault/save` | POST | api_v2_vault_save |
| `/api/v2/vault/load` | POST | api_v2_vault_load |
| `/api/v2/vault/delete` | POST | api_v2_vault_delete |
| `/api/v2/vault/list` | GET | api_v2_vault_list |
| `/api/v2/beta/profile` | POST | api_v2_beta_profile |
| `/api/v2/beta/chat/draft` | POST | api_v2_beta_chat_draft |
| `/api/v2/beta/feedback` | POST | api_v2_beta_feedback |
| `/api/v2/beta/usage` | GET | api_v2_beta_usage |

**rectification_app.py (port 5051):** `/health`, +3 rectification route

Başlatma:
```bash
.venv/bin/flask --app app run --host 127.0.0.1 --port 5000
.venv/bin/flask --app rectification_app:rectification_app run --host 127.0.0.1 --port 5051
```

### 1.3 JSON var, markdown ayrı katman

**API ham JSON döndürüyor.** Markdown, aynı chart veri modelinden
üretilen ayrı bir render/persistence katmanı.

Markdown üretim zinciri (tek renderer yok):
- `_markdown_table()` — app.py:14522 (ortak tablo)
- `_build_natal_markdown()` — app.py:17119 (kişi dosyası)
- `_build_expert_copy_markdown()` — app.py:16901 (uzman paketi)
- `_build_career_analysis_data_package_markdown()` — app.py:17404
- `_save_analysis_data_packages()` — app.py:21952 (13 paket toplu)

**PWA için kritik sonuç: uygulama Gemini'ye hiç gitmeden zengin harita
ekranı çizebilir.** Her ekran LLM istemiyor. Bu maliyet planını
kökten rahatlatıyor.

### 1.4 Yoga motoru — ID var, RUL- bağlantısı yok

`_yoga_match()` (app.py:8748) **her eşleşmeye zaten id koyuyor**:
`rajayoga_k10_t5`, `neecha_bhanga_mars` gibi motor içi dinamik kimlik.

Toplayıcı: `_build_yogas()` — app.py:9575
Kariyer tablosu satırları: `_career_yoga_rows()` — app.py:16549

**10 builder ailesi, 14 benzersiz yoga adı:**

Gaja Kesari · Kemadruma · Pancha Mahapurusha (Ruchaka/Bhadra/Hamsa/
Malavya/Shasha) · Neecha Bhanga · Viparita Rajayoga · Dhana Yoga ·
Rajayoga · Parivartana Yoga · Budha-Aditya · Chandra-Mangala

Örnek kural (Rajayoga, app.py:9080):
- ID: `rajayoga_k{kendra}_t{trikona}`
- Koşul: kendra lordu ile trikona lordu aynı lord veya aynı evde
- Konu: career | Etki: supportive
- Güç: aynı lord → medium, aynı ev → weak | Güven: low

**Kurallar tek registry'de DEĞİL** — 10 ayrı builder fonksiyonunda
dağınık `if` blokları. Ama çıktı şeması `_yoga_match()`'te,
çağrı `_build_yogas()`'ta merkezileşmiş.

**Yapı haricî `rule_id` alanı eklemeye müsait. Bağlantı şu an yok.**

`match["rule"]` sütunu builder'larda sabit İngilizce string; doğal dil
üretimi yok.

### 1.5 rules.csv — 763×26, kısmen yapısal

Sütunlar:
```
rule_id, rule_name, derived_from_claims, scope, required_inputs,
activation_conditions, supporting_conditions, counter_conditions,
exclusions, weight, confidence, school_filter, supporting_cases,
counter_cases, conflict_ids, ethical_constraints, status, version,
notes, canonical_rule_id, parent_rule_id, rule_family_id,
implementation_scope, deprecated_by, canonical_status,
conflict_link_status
```

Koşullar ayrı sütunlarda AMA hücre içerikleri `|` ile ayrılmış
sembolik düz metin — çalıştırılabilir AST/JSON koşul modeli değil.

**KRİTİK GÖZLEM: 763 kural iki farklı türden oluşuyor.**

İlk satırlar:
```
RUL-GR-0001 | Doğal ve işlevsel rolü ayır
RUL-GR-0002 | Her lordluğu ayrı koru
RUL-GR-0003 | Rol ve kapasiteyi ayır
```

Bunlar **haritadan tetiklenen kural değil, metodoloji ilkesi.**
Her analizde geçerli.

| Tür | Deterministik seçilebilir mi? |
|---|---|
| Metodoloji ilkeleri (RUL-GR gibi) | Hayır — hep geçerli. `scope` ile süzülebilir |
| Harita koşullu kurallar (RUL-T06 gibi) | Evet — yoga motoru zaten tetikliyor |

İsim eşleşmeleri (**kodsal değil, anlamsal**):
```
Rajayoga          ↔ RUL-T06-0012
Dhana Yoga        ↔ RUL-T06-0013
Pancha Mahapurusha↔ RUL-T06-0016
Kemadruma         ↔ RUL-T06-0018
Parivartana Yoga  ↔ RUL-T06-0020
Viparita Rajayoga ↔ RUL-T06-0021
Neecha Bhanga     ↔ RUL-T06-0022
```

Kod bağlantısı:
- app.py yoga motorunda rules.csv okuması **YOK**
- `dogrula_asama1.py:35` — sadece metin araması (künye var mı?)
- `olc_token.py:10` — sadece boyut ölçümü

### 1.6 Gemini entegrasyonu YOK

Aranıp bulunamadı: `google.generativeai`, `vertexai`,
`GenerativeModel`, `aiplatform`, `generate_content`, `GEMINI_API_KEY`

`requirements.txt` tamamı:
```
flask>=3.0
pyswisseph>=2.10
```

Mevcut akış **elle**: Agent Studio'ya dosya yükle → Gemini çıktısını
`/tmp/asama1.json`'a kaydet → `dogrula_asama1.py` ile doğrula.

Paket başlıklarında: `usage: "GPT sohbetine ekle"`

### 1.7 vault/load okurken YAZIYOR (mimari engel)

- Minimal chart snapshot kişi markdown'ına gömülü — app.py:11328
- **AMA** `/api/v2/vault/load` snapshot'ı kullanmıyor: doğum bilgisini
  markdown'dan okuyup haritayı **baştan hesaplıyor** — app.py:22444
- Uzman kopyası yeniden üretiliyor; yaşam olayı yoksa **13 analiz
  paketi de load sırasında yeniden yazılıyor** — app.py:29057

Sonuçları:
- Her "kaydı aç" 5.76 sn CPU yakıyor
- Her okuma 13 dosya yazıyor → Cloud Run'da dosya sistemi geçici,
  bu model çalışmaz
- Motor sürümü değişince sonuç sessizce değişebilir

**Konuştuğumuz "harita önbelleği" aslında burada. Snapshot zaten var,
sadece kullanılmıyor. Yeni sistem değil, var olanı devreye alma işi.**

### 1.8 Dağıtım hazırlığı

- Dockerfile: YOK
- .env: YOK
- Ayrı config dosyası: YOK (app.py içinde + `PROGRESIF_*` env değişkenleri)
- Beta profilleri için varsayılan SQLite yolu var
- Secret/API key tanımı bulunmadı
- Kalıcı runtime log sistemi YOK

Ölçüm: 49.4 sn → 5.76 sn (life_period_analysis tekilleştirmesi sonrası)

---

## 2. MALİYET — DÜZELTİLMİŞ HESAPLAR

### 2.1 İlk hesabım yanlıştı (düzeltildi)

15K girdi + 3K çıktı, Gemini 3.5 Flash ($1.50 / $9.00 per 1M):

| | Paket başı | 13 paket |
|---|---|---|
| İlk iddiam (YANLIŞ) | $0.027 | $0.35 |
| Doğru hesap | $0.0495 | **$0.64** |
| Batch %50 | $0.0248 | **$0.32** |

Hatanın nedeni önemli: **girdi 96K'dan 15K'ya inince çıktı, girdiden
pahalı hale geliyor** ($0.027 > $0.0225). Kaldıraç sırası değişiyor.

### 2.2 Thinking token'ları — ikimiz de kaçırmıştık

Gemini 3.5 Flash **varsayılan olarak "medium thinking effort"** ile
çalışıyor ve **düşünme token'ları çıktı fiyatından faturalanıyor**.

Aşama 1 (kural eşleştirme, karşı kanıt tartma, şema doldurma) modelin
çok düşüneceği bir iş. 3K görünür çıktının arkasında 5-8K düşünme
token'ı sürpriz olmaz.

| Senaryo | Paket başı | 13 paket |
|---|---|---|
| Thinking dahil gerçekçi | ~$0.08 | **~$1.07** |
| Thinking dahil + batch | ~$0.04 | ~$0.54 |

**Gerçek durum her iki tahminden de kötü.**

### 2.3 Düzeltilmiş kaldıraç sırası

1. **Thinking budget kontrolü** — Aşama 2 için minimal/kapalı
   (saf çeviri işi), Aşama 1 için ölçerek ayarla
2. **max_output_tokens tavanı** — maliyet + kaçak yanıt koruması
3. Kural süzme (girdi azaltma)
4. Batch (sürüm yenilemede toplu üretim)
5. Context caching (en son katman)

### 2.4 Kural süzme hedefi — mütevazileştirildi

Metodoloji ilkeleri (RUL-GR ailesi) atılamaz, her analizde geçerli.
Ama `scope`, `implementation_scope`, `school_filter`, `status`,
`deprecated_by` sütunlarıyla filtreleme mümkün.

**Gerçekçi hedef: 96K → 30-40K (2-3x), 15K (19x) değil.**

### 2.5 Model notu

Gemini 3.6 Flash (21 Temmuz 2026) $1.50 / **$7.50** — 3.5 Flash'ın
$9.00 çıktısından %17 ucuz. En pahalı kalem çıktı olduğu için
doğrudan tasarruf. Vertex'te erişim kontrol edilmeli.

Gemini 3.5 Flash-Lite: $0.30 / $2.50 — Aşama 2 için aday.

---

## 3. TEKNİK TUZAKLAR (kod yazmadan önce bilinmeli)

### 3.1 response_schema şemayı reddeder

Schema v2.2.0 `additionalProperties: false` kullanıyor.
Vertex'in `response_schema`'sı OpenAPI 3.0'ın **alt kümesi** —
`additionalProperties` ve `anyOf` yok.

**`response_json_schema` kullanılmalı** (Gemini 2.5+ tam JSON Schema
destekliyor). Aksi halde şema sessizce yok sayılır.

### 3.2 Alan sıralaması eşleşmeli

Prompt'taki şema örnekleri ile gerçek `responseSchema`'nın alan
sıralaması aynı olmalı; uyuşmazlık modeli şaşırtıp hatalı çıktıya
yol açıyor.

### 3.3 Explicit cache maliyeti

Explicit caching'de saatlik depolama ücreti var (1M token = ~$1/saat).
Silinmeyen cache günde ~$24 yakar. Düşük trafikte implicit yeterli.

### 3.4 Markdown'ı JSON'a çevirmek token ARTIRIR

Aynı veri JSON'da ~%15-20 daha fazla token. Paketleri JSON'a çevirme
önerisi (ChatGPT'den geldi) reddedildi — hem token artırır hem
107/107 testi geçen yapıyı bozar.

**Karar: markdown paketler korunur, yanına ayrı künye manifestosu
eklenir.**

### 3.5 Aşama 2 birleştirilmeyecek

ChatGPT "iki aşamayı tek çağrıda birleştir" önerdi. **Reddedildi.**
Aşama 2'nin veri paketine erişememesi halüsinasyon duvarının kendisi.
Birleştirme bu güvenceyi yok eder. (Şablon renderer ve Flash-Lite
seçenekleri geçerli.)

### 3.6 Fingerprint eksik

"Doğum verisini hash'le" yetersiz. Aynı doğum verisi farklı ayanamsa
veya motor sürümünde farklı sonuç üretir.

Chart fingerprint içermeli:
```
doğum tarihi + saat + koordinat + timezone (+ tz veri sürümü)
+ ayanamsa + node tipi + ephemeris sürümü + motor sürümü
+ varga ayarları + orb/açı ayarları
```

Analiz cache anahtarı ayrıca:
```
chart_fingerprint + topic + methodology_version + ruleset_version
+ prompt_version + schema_version + model_id + language + mode
```

---

## 4. ÖNCELİK LİSTESİ

| # | İş | Kim | Neden |
|---|---|---|---|
| 1 | **Git commit + uzak yedek** | Levent | 3 aylık iş korumasız |
| 2 | `vault/load` okurken yazmayı bıraksın, snapshot'tan okusun | Codex | Bulutun önkoşulu + hız |
| 3 | `_yoga_match()`'e `rule_id` alanı ekle (boş bırakılabilir) | Codex | Tek nokta, küçük iş |
| 4 | 14 yoga → RUL- künye eşleme tablosu | **Levent** | Astroloji kararı, Codex yapamaz |
| 5 | rules.csv scope/topic süzme fonksiyonu | Codex | Girdi azaltma |
| 6 | Gemini programatik entegrasyonu | Codex | Zincirin eksik halkası |
| 7 | Cloud Run + Dockerfile | Codex | Dağıtım |

3 ve 4 paralel yürüyebilir: Codex alanı açar, Levent doldurur.

---

## 5. HEDEF MİMARİ

```
PWA / Mobil
     │
     ▼
Cloud Run: Flask API (app.py)
     │
     ├─ Harita önbelleği (fingerprint anahtarlı)
     │    vardır → oku | yoktur → hesapla, yaz
     │    [şu an snapshot var ama kullanılmıyor]
     │
     ├─ Paket üretici (markdown) + künye manifestosu
     │
     ├─ İlk açılışta üretim (lazy generation):
     │    kayıtta sadece harita + omurga özeti
     │    konu analizi ilk açılışta üret ve sakla
     │
     ├─ Vertex AI Gemini
     │    Aşama 1: teknik JSON (response_json_schema)
     │    Aşama 2: danışan dili (izole, Flash-Lite/şablon)
     │
     └─ Serbest sohbet: canlı çağrı + RAG (kaynak/ekol soruları)
```

Ekran açmak = veritabanı okuması. LLM sadece iki anda:
kayıt/ilk açılış (bir kez) ve serbest soru (seyrek).

---

## 6. AÇIK SORULAR

1. `rules.csv`'de `scope`, `implementation_scope`, `school_filter`,
   `status` sütunlarının **benzersiz değerleri ve dağılımı** nedir?
   → Süzme stratejisi buna bağlı. Codex'e sorulacak.
2. Vertex'te hangi modellere erişim var? (3.6 Flash, Flash-Lite)
3. Supabase kullanılıyor mu? (ChatGPT öyle varsaydı, **doğrulanmadı**)
   → Firestore/Postgres kararını belirliyor.
4. API v2 neden `CLAUDE.md`'ye yansımamış? İki iş kolu birbirinden
   habersiz mi ilerledi?
5. Vault'ta kişi "leo" ve "levo" — aynı kişi mi, ayrı kayıt mı?
6. `SYSTEM_METHODOLOGY` tam metni hâlâ okunmadı.
7. v1 sağlık paketi mağaza/KVKK açısından ayrı ele alınmalı mı,
   yoksa v1'de hiç yayınlanmasın mı?

---

## 7. REDDEDİLEN ÖNERİLER (tekrar gündeme gelmesin)

| Öneri | Kaynak | Red gerekçesi |
|---|---|---|
| Aşama 1+2'yi tek çağrıda birleştir | ChatGPT | Halüsinasyon duvarını yıkar |
| Markdown paketleri JSON'a çevir | ChatGPT | Token artırır, test edilmiş yapıyı bozar |
| 13 paketi kayıtta toplu üret | Claude (ilk plan) | Açılmayacak rapora ödeme; lazy generation daha iyi |
| Deterministik seçim RAG'i tamamen gereksiz kılar | Claude (ilk plan) | Serbest sorular için RAG gerekli |
| Client-side Swiss Ephemeris (WASM) | Claude (ilk plan) | 29K satırlık motor porte edilemez; sadece görsel çizim için düşünülebilir |

---

## 8. DÜZELTME KAYDI

Bu oturumda kabul edilen hatalar:

1. **Maliyet hesabı yanlıştı** — $0.35/$0.18 dedim, doğrusu
   $0.64/$0.32. ChatGPT düzeltti, doğru.
2. **"app.py kural izlemiyor" çıkarımı eksikti** — künye izlemiyor
   ama kendi yoga motoru ID üretiyor. Vault çıktıları görülünce
   düzeltildi.
3. **"API v2 kodlanmamış" varsayımı yanlıştı** — kodlanmış, hem de
   tasarımın ötesinde.
4. **Cache anahtarı önerisi eksikti** — sadece doğum verisi yetmez,
   ayanamsa + ephemeris + motor sürümü şart.
5. **Thinking token'ları hiç hesaba katılmamıştı** — en büyük kalem.
6. **RAG'i fazla keskin dışladım** — serbest sorular için gerekli.

---

*Son güncelleme: 2026-07-29*
