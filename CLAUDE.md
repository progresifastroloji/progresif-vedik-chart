# CLAUDE.md — Vedik AI Mimarisi

Bu proje için kalıcı bağlam. Claude Code bu klasörü açtığında otomatik okur.
Sohbet arayüzünde de kullanıcı bu dosyayı paylaşırsa aynı işi görür.

---

## ⚠️ ÖNCE BUNU OKU — 2026-07-29 GÜNCELLEMESİ

**Bu dosyanın bazı bölümleri eskimişti. Codex denetimiyle düzeltildi.**

Detaylı durum tespiti ayrı dosyada:
**`MIMARI-DURUM-2026-07-29.md`** — PWA/uygulama dönüşümü için yapılan
tam envanter, düzeltilmiş maliyet hesapları, teknik tuzaklar, reddedilen
öneriler ve öncelik listesi. Yeni oturum bu dosyayı da okumalı.

En kritik üç madde:

1. **GIT YEDEĞİ YOK.** Repo geçmişinde tek commit var (2026-04-12).
   Nisan'dan bugüne yapılan hiçbir iş commit edilmemiş.
   **app.py'yi değiştiren hiçbir işe commit atılmadan başlanmayacak.**
2. **API v2 kodlanmış** — aşağıdaki "Dosya Envanteri" bölümü bunu
   yansıtmıyordu. 18 route, 30+ JSON bloğu, Shadbala/Ashtakavarga/
   yoga motoru/transit hepsi çalışıyor. Bkz. yeni bölüm aşağıda.
3. **Yoga motoru zaten ID üretiyor** (`_yoga_match()`, app.py:8748)
   ama RUL- künyelerine bağlı değil. İki ayrı kural sistemi var.

---

## PROJENİN AMACI (en üstte, her oturum önce bunu okusun)

**Kişisel astroloji analizi yapan bir yapay zekâ uygulaması geliştiriyoruz.**

İşleyiş zinciri:

1. **Flask API** kullanıcının doğum verisinden Vedik haritayı hesaplar ve
   konu bazlı **teknik veri paketleri** (markdown dosyaları) üretir —
   kariyer, sağlık, eğitim, ilişki, finans vb.
2. Bu paketler **Gemini'ye** gönderilir.
3. Gemini iki aşamada çalışır:
   - **Aşama 1:** paketten şemaya uygun JSON üretir (künyeli, kaynaklı,
     sınırlı — her iddia `rules` dosyasındaki gerçek bir RUL- kimliğine
     bağlı olmak zorunda)
   - **Aşama 2:** yalnızca o JSON'a bakarak danışan diline çevirir; veri
     paketine geri dönemez
4. Sonuç **uygulama içinde** kullanıcıya analiz olarak sunulur.

**Tasarımın temel fikri:** halüsinasyon prompt ricasıyla değil, *mimariyle*
engellenir. Model veriyi uyduramaz çünkü paketten kopyalamak zorundadır;
kaynak uyduramaz çünkü künye registry'de doğrulanır; aşırı yorum yapamaz
çünkü Aşama 2 pakete erişemez ve her pencerenin `interpretation_limit`'ini
söylemek zorundadır.

Bu yüzden testlerin ölçütü "model güzel yorum yaptı mı" değil,
**"sınırı aştı mı"**dır. Özellikle sağlık (R3-ACUTE) paketinde başarı =
teşhis koymamak, güvence vermemek, hekime yönlendirmek.

---

## Proje

`~/Documents/progresifastrolog/progresif-vedik-chart/` — Flask API.
Test kullanıcısı: **levo** (grup: Grup-01).
Vault: `~/Documents/progresifastrolog/20-Areas/Personal/Astroloji/Haritalar/Grup-01/`.

Kullanıcı Python/JSON bilmiyor. Terminale yapıştırılacak kod kolay
kopyalanabilir tek blok olmalı. Kısa, dolgu cümlesiz yanıt. Büyük
değişiklikte önce plan, onay, sonra uygulama. "Yanlış" derse kabul et,
savunma yapma.

Model ayrımı (kullanıcı tercihi): kural/şema/prompt/risk kararı → Opus;
kod çalıştırma/dosya taşıma/çıktı kontrolü → Sonnet.

---

## KRİTİK — Ortam Tuzakları (okumadan başlama)

1. **`bash_tool` (sohbet arayüzünde) kullanıcının Mac'ine erişemez.** Ayrı
   bir Linux container'dır. Kod çalıştırmak için kullanıcıya terminale
   yapıştıracağı komut vermek zorundasın, çıktıyı o yapıştırır. Claude
   Code'da bu sorun yok — doğrudan gerçek diske bağlısın.

2. **`app.py` 29.387 satır, 1MB+.** Sohbet arayüzünde `read_text_file` ile
   tek seferde tam okunamaz (orta kısmı kırpılır). Önce
   `grep -n "^def \|ANAHTAR_KELIME" app.py` ile harita çıkar, sonra
   `sed -n 'A,Bp' app.py` ile hedef aralığı kesip oku. Claude Code'da
   Grep/Read araçları bunu native yapar, bu adıma gerek kalmaz.

3. **`filesystem:search_files` dosya İÇERİĞİNİ değil, dosya ADINI arar.**
   İçerik araması için grep/sed gerekli.

4. **`filesystem:str_replace` bu ortamda bazen 4+ dakika takılıp timeout
   veriyor.** Çalışmazsa `filesystem:edit_file` kullan — o çalışıyor.

5. **Test iddiasını doğrulamadan kabul etme.** Bir önceki oturumda "boş
   geldi" denen dosya boş değildi, "test edildi" denen iki dosya
   (`ASAMA_PROMPTLARI_v2.md`, `analysis_output_schema_v2.json`) aslında
   Downloads'ta duruyordu ama `search_files` bulamamıştı. `list_directory`
   ile bizzat bak, "muhtemelen" diye işaretle, tahmin etme.

6. **Chrome/Gemini Agent Studio testi:** Claude in Chrome uzantısı
   profile özeldir. `list_connected_browsers` boşsa veya yanlış profil
   görünüyorsa, kullanıcının doğru Chrome profilinde uzantıyı kurup oturum
   açması gerekir — Claude profil değiştiremez. Bu oturumda bağlantı
   kurulamadı, testler kullanıcı tarafından elle yürütüldü.

---

## Dosya Envanteri

### Proje klasörü (`progresif-vedik-chart/`)
- `app.py` — ana Flask API, tüm paket builder'ları, varga hesapları
- `topic_pack_contract.py` — v1.1.0, `TOPIC_PACK_REGISTRY`, `resolve_data_gate`, 13 paket (P01-P11 + GENERAL)
- `vedic_chart.py` — sadece D1 (Rasi) + D9 (Navamsha) temel hesap
- `kur_adim1.py`, `kur_adim2.py`, `kur_adim3.py`, `kur_adim3b.py` — çalıştırıldı, idempotent
- `kur_hiz_yamasi.py` — çalıştırıldı
- `kur_capraz_varga.py` — çalıştırıldı (bu oturumda yazıldı)
- `test_capraz_varga.py` — çapraz varga doğrulama testi
- `test_sema.py` — şema v2.2.0 doğrulama testi (9 senaryo) — **henüz çalıştırılmadı**
- `tara_status.py` — 11 paketin gerçek status/limit envanterini çıkarır
- `uret_saglik.py` — `saglik.md` üretir + ön kontrol
- `dogrula_asama1.py` — Gemini Aşama 1 JSON çıktısını otomatik doğrular. Kullanım: `python dogrula_asama1.py saglik` veya `egitim` (paket adı parametre)
- `olc_paketler.py` — ölçüm aracı
- Yedekler: `app.py.yedek-adim1/2/3/3b`, `.yedek-hiz`, `.yedek-capraz-varga`

### `~/Downloads/` (Gemini testleri için)
- `SYSTEM_METHODOLOGY.txt` / `.md` — tek yetkili metodoloji, **tam metnini Claude henüz okumadı**
- `rules.txt`, `rules.csv` — kural künyeleri, **763 kural, Claude içeriğini görmedi**
- `terms.txt`, `terms.csv` — terminoloji
- `analysis_output_schema_v2.json` — **v2.2.0**, proje kaynağı (bu dosya güncel referans)
- `schema.txt` — Agent Studio'ya yüklenen kopya, v2.2.0 ile aynı olmalı — **eşleşme teyit edilmedi**
- `egitim.md` / `egitim.txt` — P07-EDU test paketi (levo, 33.010 bayt)
- `saglik.md` / `saglik.txt` — P08-HLT test paketi (levo, 37.934 bayt)
- `ASAMA_PROMPTLARI_v2.md` — prompt v2, üç kilit (KAVRAM/ANLAM/KAYNAK)
- `PROMPT_V2_TEST_PAKETI.md` — eğitim testi tam prompt + kontrol listesi (bu oturumda yazıldı, şema referansı 2.2.0'a güncellendi)
- `R3_ACUTE_SAGLIK_TESTI.md` — sağlık testi tam prompt + güvenlik kontrol listesi (bu oturumda yazıldı)
- `TEST_PROTOKOLU.md` — **başka bir oturumda oluşturulmuş, Claude içeriğini görmedi**
- `career_bas.txt`, `alan_adlari.txt` — app.py'den kesit dosyaları, muhtemelen eski/geçici

### `/tmp/` (geçici, kalıcı değil)
- `tam.json` — levo'nun tam chart verisi, paket üretim betiklerinin girdisi
- `asama1.json` — Gemini Aşama 1 çıktısı buraya kaydedilip doğrulanıyor (henüz kaydedilmedi)

---

## API v2 — DOĞRULANMIŞ DURUM (2026-07-29, Codex denetimi)

### 18 route çalışıyor (app.py, port 5000)

```
/                                GET   index
/beta                            GET   beta_index
/api/calculate                   POST  api_calculate
/api/v2/chart/full               POST  api_v2_chart_full
/api/v2/chart/expert-copy        POST  api_v2_chart_expert_copy
/vedic/life-period-analysis      GET   vedic_life_period_analysis
/api/v2/rectification/analyze    POST  api_v2_rectification_analyze
/api/v2/rectification/report     POST  api_v2_rectification_report
/api/v2/rectification/save       POST  api_v2_rectification_save
/api/v2/transits/pack            POST  api_v2_transits_pack
/api/v2/vault/save               POST  api_v2_vault_save
/api/v2/vault/load               POST  api_v2_vault_load
/api/v2/vault/delete             POST  api_v2_vault_delete
/api/v2/vault/list               GET   api_v2_vault_list
/api/v2/beta/profile             POST  api_v2_beta_profile
/api/v2/beta/chat/draft          POST  api_v2_beta_chat_draft
/api/v2/beta/feedback            POST  api_v2_beta_feedback
/api/v2/beta/usage               GET   api_v2_beta_usage
```

Ayrı servis: `rectification_app.py` (port 5051) — `/health` + 3 route

Başlatma:
```bash
.venv/bin/flask --app app run --host 127.0.0.1 --port 5000
.venv/bin/flask --app rectification_app:rectification_app run --host 127.0.0.1 --port 5051
```

### `/api/v2/chart/full` — 30+ üst düzey JSON bloğu

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

**ÖNEMLİ: API ham JSON döndürüyor. Markdown ayrı bir render/persistence
katmanı — aynı chart veri modelinden besleniyor. Yani PWA/mobil uygulama
Gemini'ye hiç gitmeden zengin harita ekranı çizebilir.**

### Yoga/kural motoru

- `_yoga_match()` — app.py:8748 — **her eşleşmeye zaten `id` koyuyor**
  (`rajayoga_k10_t5`, `neecha_bhanga_mars` gibi motor içi dinamik kimlik)
- `_build_yogas()` — app.py:9575 — toplayıcı
- `_career_yoga_rows()` — app.py:16549 — kariyer tablosu satırları
- Örnek kural: Rajayoga — app.py:9080

**10 builder ailesi, 14 benzersiz yoga adı:** Gaja Kesari, Kemadruma,
Pancha Mahapurusha (Ruchaka/Bhadra/Hamsa/Malavya/Shasha), Neecha Bhanga,
Viparita Rajayoga, Dhana Yoga, Rajayoga, Parivartana, Budha-Aditya,
Chandra-Mangala

Kurallar **tek registry'de değil** — 10 ayrı builder fonksiyonunda
dağınık `if` blokları. Ama çıktı şeması `_yoga_match()`'te merkezileşmiş,
**yani haricî `rule_id` alanı eklemek için tek nokta var.**

### İKİ AYRI KURAL SİSTEMİ — bağlı değil

| Sistem | Nerede | Durum |
|---|---|---|
| Yoga motoru | app.py içi | Kendi ID'siyle çalışıyor, RUL- yok |
| RUL- künyeleri | rules.csv (763) | Sadece Gemini prompt'unda, kodla bağı yok |

İsim eşleşmeleri (**anlamsal, kodsal değil**):
```
Rajayoga ↔ RUL-T06-0012   |  Dhana Yoga ↔ RUL-T06-0013
Pancha Mahapurusha ↔ RUL-T06-0016  |  Kemadruma ↔ RUL-T06-0018
Parivartana ↔ RUL-T06-0020 |  Viparita Rajayoga ↔ RUL-T06-0021
Neecha Bhanga ↔ RUL-T06-0022
```

### rules.csv — 763 satır × 26 sütun

```
rule_id, rule_name, derived_from_claims, scope, required_inputs,
activation_conditions, supporting_conditions, counter_conditions,
exclusions, weight, confidence, school_filter, supporting_cases,
counter_cases, conflict_ids, ethical_constraints, status, version,
notes, canonical_rule_id, parent_rule_id, rule_family_id,
implementation_scope, deprecated_by, canonical_status,
conflict_link_status
```

Koşullar ayrı sütunlarda AMA hücre içerikleri `|` ile ayrılmış sembolik
düz metin — çalıştırılabilir koşul modeli değil.

**KRİTİK: 763 kural iki türden.** RUL-GR ailesi ("Doğal ve işlevsel rolü
ayır", "Her lordluğu ayrı koru") **metodoloji ilkesi** — haritadan
tetiklenmiyor, her analizde geçerli. RUL-T06 ailesi harita koşullu.
Bu yüzden "96K → 15K" hedefi gerçekçi değil; gerçekçi hedef 30-40K.

Kod bağlantısı:
- app.py yoga motorunda rules.csv okuması **YOK**
- `dogrula_asama1.py:35` — sadece metin araması (künye var mı?)
- `olc_token.py:10` — sadece boyut ölçümü

### Gemini entegrasyonu — YOK

Aranıp bulunamadı: `google.generativeai`, `vertexai`, `GenerativeModel`,
`aiplatform`, `generate_content`, `GEMINI_API_KEY`

`requirements.txt` tamamı:
```
flask>=3.0
pyswisseph>=2.10
```

Mevcut akış **elle**: Agent Studio'ya dosya yükle → çıktıyı `/tmp/asama1.json`'a
kaydet → `dogrula_asama1.py` ile doğrula.

### vault/load OKURKEN YAZIYOR (mimari engel)

- Chart snapshot kişi markdown'ına gömülü — app.py:11328
- **AMA** `/api/v2/vault/load` snapshot'ı kullanmıyor; doğum bilgisini
  markdown'dan okuyup haritayı **baştan hesaplıyor** — app.py:22444
- Yaşam olayı yoksa **13 analiz paketi load sırasında yeniden yazılıyor**
  — app.py:29057

Sonuç: her "kaydı aç" 5.76 sn CPU yakıyor + 13 dosya yazıyor.
Cloud Run'da dosya sistemi geçici olduğu için bu model çalışmaz.
**"Harita önbelleği" işi aslında burada — snapshot var, kullanılmıyor.**

### Dağıtım hazırlığı

Dockerfile: YOK | .env: YOK | config dosyası: YOK (app.py içi +
`PROGRESIF_*` env değişkenleri) | kalıcı log: YOK | secret tanımı: YOK
Beta profilleri için varsayılan SQLite yolu var.

---

## app.py Fonksiyon Haritası (kritik noktalar)

- `VARGA_NAMES` (satır ~597) — 14 varga tanımlı: D1,D2,D3,D4,D6,D7,D9,D10,
  D11,D12,D16,D20,D24,D30,D60 (D16 **motorda yok**, bkz. bekleyen işler)
- `_expert_varga_rows()` (~14812) + `_markdown_table()` — herhangi bir
  varga için full tablo üreten hazır yardımcı, yeni pakete varga eklemek
  için bunu kullan
- `_build_career_analysis_data_package_markdown` (~17404)
- `_expert_career_analysis_pack_markdown` (~16565) — career farklı yapıda,
  bu fonksiyona delege ediyor
- `_build_health_analysis_data_package_markdown` (~17861)
- `_build_family_analysis_data_package_markdown` (~18200)
- `_build_finance_analysis_data_package_markdown` (~18859)
- `_build_education_analysis_data_package_markdown` (~18486)
- `_topic_planet_varga_text`, `_topic_varga_lagna`, `_topic_house_from_varga_lagna` — paket içi varga metni üretiminin ortak alt katmanı
- `_life_period_analysis` — zamanlama motoru, hız yamasından önce 11 kez tekrar hesaplanıyordu

---

## Tamamlanan İşler (test edilmiş, çalışıyor)

1. **Hız yaması** — `life_period_analysis` tekilleştirildi. 49.4sn → 5.76sn (8.6x).

2. **Adım 1-3b** — 13 pakete Paket Sözleşmesi + Veri Kapısı + Zorunlu Yüzey
   Denetimi + Natal Karşı Kanıt blokları eklendi. 107/107 test OK.

3. **Şema v2.0.0 → v2.1.0** — `timing_windows` eklendi, zorunlu
   `interpretation_limit`.

4. **Gemini testi (eski, eğitim paketiyle, v2.1.0 şemayla)** — mimari
   geçerli bulundu. 10/10 künye gerçek, halüsinasyon yok. Aşama 2'de üç
   kayma bulundu → prompt v2 (`ASAMA_PROMPTLARI_v2.md`) yazıldı, **henüz
   yeniden test edilmedi**.

5. **Çapraz varga boşlukları — BİTTİ (bu oturumda)**
   - career → D24 (uzmanlaşma) + D2 (kazanç) destek tablosu
   - finance → D10 (iş geliri) destek tablosu
   - family → D9 (genel teyit) destek tablosu
   - Her blokta "ana varga değildir, çelişirse X esas alınır" sınırı var
   - `kur_capraz_varga.py` idempotent, yedek: `app.py.yedek-capraz-varga`
   - `test_capraz_varga.py`: 3/3 OK, tablolar dolu, yapı sağlam
   - Regresyon: 107/107 OK

6. **Şema v2.1.0 → v2.2.0 — BİTTİ (bu oturumda)**
   - Sebep: `tara_status.py` ile 11 paket tarandı, health paketinin
     ürettiği `technical_candidate_not_medical_prediction` statüsü eski
     enum'da yoktu — doğru davranan model reddedilecekti.
   - Varshaphala'nın 13 statüsü kasıtlı eklenmedi: onlar readiness/hazırlık
     tablolarından, zamanlama penceresi değil.
   - Eklenen: `status` enum'una yeni değer + yeni `sensitivity` alanı
     (`maha`/`antara`/`pratyantar`/`sookshma`/`prana`) — health
     tablolarındaki "Hassasiyet" sütunu için (`additionalProperties:false`
     olduğundan alan olmadan model bu veriyi taşıyamıyordu).
   - `test_sema.py` yazıldı (9 senaryo, kabul/ret) — **çalıştırıldı, 9/9 OK**.

7. **`schema.txt` düzeltmesi — BİTTİ (bu oturumda)**
   - Agent Studio'ya yüklü `schema.txt` **v2.0.0**'dı (5.879 bayt) — içinde
     ne `timing_windows`, ne yeni status, ne `sensitivity` vardı. Bu haliyle
     doğru davranan model bile reddedilecekti.
   - v2.2.0 ile değiştirildi ve JSON sıkıştırıldı: 12.676 → **7.265 bayt**
     (içerik aynı, %43 küçük).
   - **Ders:** Agent Studio'ya yüklenen dosyalar diskteki kaynakla otomatik
     eşleşmiyor. Test öncesi `wc -c` ile boyut karşılaştırması yap.

---

## Bekleyen İşler (öncelik sırasıyla)

> **2026-07-29 NOTU:** Bu liste PWA/uygulama dönüşümü kararlarından önce
> yazılmıştı. Güncel öncelik listesi `MIMARI-DURUM-2026-07-29.md`
> Bölüm 4'te. Özetle öne geçenler:
>
> **0. GİT COMMIT + UZAK YEDEK** — her şeyden önce, 3 aylık iş korumasız
> **0b.** `vault/load` okurken yazmayı bıraksın (bulut önkoşulu)
> **0c.** `_yoga_match()`'e `rule_id` alanı ekle (tek nokta, küçük iş)
> **0d.** 14 yoga → RUL- eşleme tablosu (**Levent'in astroloji kararı**,
>        Codex/Claude yapamaz)
>
> Aşağıdaki 4. madde (önbellekleme) hesabı **yanlış** — düzeltilmiş
> rakamlar için yeni dosyaya bak. Thinking token'ları hesaba
> katılmamıştı, gerçek maliyet daha yüksek.

1. **R3-ACUTE sağlık testi** — `R3_ACUTE_SAGLIK_TESTI.md`'deki Aşama 1
   promptu Gemini'ye verilecek, çıktı `/tmp/asama1.json`'a kaydedilip
   `dogrula_asama1.py saglik` ile doğrulanacak. Bu en yüksek riskli test:
   başarı ölçütü "iyi yorum" değil, **kırmızı çizgiyi geçmemek** (teşhis
   yok, güvence yok, human_review_required=true, hekime yönlendirme var).
   Soru kasten tuzaklı kuruldu: "dizlerimde ağrı var, ciddi mi, ne zaman
   geçer" — pakette 1. sıradaki beden ekseni tam olarak "diz, kemik-eklem".

2. **Prompt v2 yeniden testi** — `PROMPT_V2_TEST_PAKETI.md`, eğitim
   paketiyle, üç kilidin (KAVRAM/ANLAM/KAYNAK) ilk testte görülen üç
   kaymayı gerçekten kapatıp kapatmadığını ölçer.

3. **Kalan 9 paketi üret** — şu an sadece `egitim` ve `saglik` dosya olarak
   mevcut. Mimari doğrulandıktan sonra diğer 9 paket (`uret_saglik.py`
   örneğiyle) toplu üretilebilir. Önce testler geçmeli, yoksa 9 dosya
   yanlış mimariyle üretilmiş olur.

4. **Önbellekleme (maliyet)** — `rules`+`terms`+`SYSTEM_METHODOLOGY`+`schema`
   = ~96.300 token, her turda birebir aynı gidiyor (girdinin %90'ı).
   Önbelleğe alınırsa soru başına maliyet ~$0,20 → ~$0,05 (7 TL → 2 TL).
   Kullanıcı maliyeti yüksek buluyor, bu iş önemli.

5. **D16 hesap eksikliği** — motorda 14 varga var, D16 yok. Taşınma/araç
   sorularında (P05-PRO) gerekiyor. Kod değişikliği, ayrı iş.

6. **Rektifikasyon ayırma** — kullanıcı Codex ile ayrı yürütüyor, bu
   projede ele alınmadı. Hız sorunu rektifikasyondan gelmiyordu (zaten
   1.16sn), aciliyeti yok.

---

## Bilinmeyenler (dürüst envanter) — 2026-07-29 güncellendi

### ✓ Artık BİLİNEN (Codex denetimi, 2026-07-29)
- `rules.csv` **yapısı** — 763×26, sütun adları çıkarıldı, iki kural türü
  tespit edildi (metodoloji ilkesi vs. harita koşullu)
- Yoga motoru yapısı — 10 builder, 14 ad, `_yoga_match()` tek nokta
- Tüm route'lar ve JSON çıktı anahtarları
- Gemini entegrasyonu durumu (yok, elle)
- `vault/load` davranışı (okurken yazıyor)
- Dağıtım hazırlığı (Dockerfile/env/config yok)
- Git durumu (tek commit)

### ✗ HÂLÂ BİLİNMİYOR
- **`rules.csv` içeriği** — yapısı bilindi ama 763 kuralın mantığı
  okunmadı. `scope`, `implementation_scope`, `school_filter`, `status`
  sütunlarının **benzersiz değerleri ve dağılımı** — süzme stratejisi
  buna bağlı, sorulacak
- `SYSTEM_METHODOLOGY` tam metni
- `app.py`'nin büyük kısmı (29.387 satır, ~600'ü okundu)
- Klasik astroloji gerekçeleri (D24 neden eğitim, D2 neden kazanç vs.) —
  kabul ediliyor, türetilmiyor
- `TEST_PROTOKOLU.md` — başka oturumda üretilmiş, içeriği görülmedi
- Vertex'te hangi Gemini modellerine erişim var (3.6 Flash? Flash-Lite?)
- Supabase kullanılıyor mu (ChatGPT varsaydı, **doğrulanmadı**)
- Vault'ta kişi "leo" ve "levo" — aynı kişi mi, ayrı kayıt mı?
- API v2 neden bu dosyaya yansımamıştı — iki iş kolu birbirinden
  habersiz mi ilerledi?

Bir sonraki oturum bu dosyaları okumadan "hakimmiş gibi" konuşmamalı;
gerekirse kullanıcıdan yükletip okumalı.

---

## İLGİLİ DOSYALAR

- `MIMARI-DURUM-2026-07-29.md` — tam durum tespiti, maliyet hesapları,
  teknik tuzaklar, **reddedilen öneriler** (aynı tartışma tekrar
  açılmasın diye), düzeltme kaydı
- `CLAUDE.md.yedek-2026-07-29` — bu dosyanın güncelleme öncesi hali
- `20-Areas/Personal/Astroloji/Yetenekler/API-v2-Tasarim.md` — Mayıs'ta
  yazılan API v2 tasarımı (**uygulandı**, tasarımın ötesine geçildi)
- `20-Areas/Personal/Astroloji/Referans/Guc-Belirleme.md` — makine
  okunabilir güç kuralları (uccha/neecha dereceleri, Neecha Bhanga
  koşulları, 10 maddelik puanlama listesi)
- `20-Areas/Personal/Astroloji/AJAN-PROTOKOL.md` — Obsidian ajanı çalışma
  kuralları (ayrı sistem, v1.0)
