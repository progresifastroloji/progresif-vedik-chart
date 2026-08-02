---
id: vedic-ai-application-v1
title: AI ve Uygulama Odaklı Vedik Metodoloji
version: 1.0.0
status: candidate
scope: vedic-jyotisha
language: tr
runtime_profile: ai-application
requires_verified_chart_data: true
allows_model_calculation: false
timing_mode: intent-gated
output_pipeline: technical-json-then-narrative
---

# AI ve Uygulama Odaklı Vedik Metodoloji

## 1. Amaç

Bu metodoloji, Vedik/Jyotisha analizini bir modelin sırasıyla, eksiksiz ve denetlenebilir biçimde uygulayabileceği çalışma sözleşmesine dönüştürür.

Astrolojik hesaplamanın sahibi uygulama veya doğrulanmış hesaplama API'sidir. Model yalnız sağlanan teknik gerçekleri sınıflandırır, ilişkilendirir, tartar ve anlatıya çevirir.

Metodoloji iki aşamalı çıktı üretir:

1. **Teknik çekirdek:** Yapılandırılmış gerçekler, kanıtlar, karşı kanıtlar, statüler ve güven düzeyi
2. **Danışan anlatısı:** Teknik çekirdeğe sadık psikolojik anlam ve rehberlik

İkinci aşama birinci aşamada bulunmayan yeni astrolojik gerçek ekleyemez.

## 2. Değiştirilemez çalışma ilkeleri

1. Lagna ve dokuz grahanın nakshatra/padaları ilk yorum katmanıdır.
2. Her gösterge için nakshatra yöneticisi ve burç dispozitörü zinciri ayrı ayrı çıkarılır.
3. D1 natal vaat ve ana yapısal omurgadır.
4. Vargalar D1'i teyit, nitelendirme veya sınırlandırma amacıyla kullanılır.
5. Ev, ev yöneticisi, yerleşen grahalar, drishti, karaka ve bağlantılı evler birlikte okunur.
6. Güç, rol, aktivasyon ve sonuç birbirinden ayrılır.
7. Daşa, transit ve Varshaphala natal vaadin zamanlama katmanlarıdır.
8. Tek göstergeden kesin hüküm üretilemez.
9. Destek, zorluk, karşı kanıt ve eksik veri görünür tutulur.
10. Teknik analiz, psikolojik anlam ve rehberlik ayrı aşamalardır.
11. Tanı, korku, garanti, kadercilik ve aşırı kesinlik yasaktır.
12. API veya veri paketinde bulunmayan astrolojik bilgi üretilemez.

## 3. Uygulama mimarisi sınırı

Önerilen çalışma zinciri:

`kullanıcı sorusu → intent router → veri gereksinimi → hesaplama API'si/veri paketi → fact validator → metodoloji yürütücüsü → teknik JSON → astrolojik validator → anlatı renderer → dil/güvenlik validatorı → kullanıcı çıktısı`

Modelin yapmaması gerekenler:

- Harita veya varga hesaplamak
- Nakshatra/pada tahmin etmek
- Drishti üretmek
- Daşa tarihlerini hesaplamak
- Eksik bala, avastha veya yıllık harita alanını tamamlamak
- Kullanılabilir veri olmadan fallback astrolojik yorum yazmak

## 4. Girdi sözleşmesi

Uygulama mümkünse aşağıdaki üst seviye yapıyı sağlamalıdır:

```json
{
  "request": {
    "request_id": "string",
    "question": "string",
    "intent": "natal|topic|past_event|period|forecast",
    "topic": "string|null",
    "target_date": "date|null",
    "language": "tr|en",
    "detail_level": "short|standard|deep"
  },
  "calculation_profile": {
    "ayanamsha": "string",
    "house_profile": "string",
    "birth_time_confidence": "exact|approximate|uncertain|unknown",
    "calculator_version": "string",
    "data_hash": "string"
  },
  "chart": {
    "d1": {},
    "nakshatras": [],
    "dispositor_chains": [],
    "drishti": [],
    "strength": {},
    "yogas": [],
    "vargas": {},
    "dashas": {},
    "transits": {},
    "varshaphala": {}
  },
  "validation_profile": {}
}
```

Alan adları uygulamanın gerçek sözleşmesine uyarlanabilir. Ancak veri kaynağı, sürüm, hash ve doğum saati güveni korunmalıdır.

## 5. Durum makinesi

Yürütme sırası sabittir:

`SCOPE_GATE → INTENT_ROUTE → DATA_PROFILE → FACT_INVENTORY → NAKSHATRA_SCAN → CHAIN_GRAPHS → D1_BACKBONE → TOPIC_MATRIX → STRENGTH → VARGA → NATAL_PROMISE → TIMING_GATE → EVIDENCE_SYNTHESIS → TECHNICAL_VALIDATION → NARRATIVE → NARRATIVE_VALIDATION → COMPLETE`

Her aşama yalnız önceki aşama başarılı veya kontrollü eksik statüsüyle sonuçlandıktan sonra çalışır.

Olası aşama statüleri:

- `PASS`: Gerekli veri ve kontrol tamam
- `PARTIAL`: Analiz sürdürülebilir, fakat açık sınırlama var
- `HOLD`: Kullanıcı veya veri kaynağından ek bilgi gerekli
- `BLOCKED`: Güvenilir hüküm üretmek mümkün değil
- `NOT_APPLICABLE`: Bu soru rotasında katman gerekmiyor

## 6. Aşama 0 — Scope gate

Kontroller:

- Çalışma yalnız Vedik/Jyotisha kapsamında mı?
- Soru bir kişinin haritasıyla mı ilgili?
- Üçüncü kişi veya hassas veri var mı?
- Sağlık, hukuk, finans veya güvenlik açısından yüksek riskli iddia riski var mı?
- Doğum saati gerekli teknikler için yeterince güvenilir mi?

Kapsam belirsizse yorum başlamaz. Hassas alanda astrolojik anlatı gerçek uzman görüşünün yerine geçirilmez.

## 7. Aşama 1 — Intent route

Intent sınıfları:

- `natal_general`
- `character`
- `career`
- `relationship`
- `family`
- `health`
- `finance`
- `education`
- `spirituality`
- `past_event`
- `period_analysis`
- `forecast`

Zamanlama yalnız `past_event`, `period_analysis` veya `forecast` rotalarında zorunlu olabilir. Diğer rotalarda kullanıcı açıkça istemedikçe çalıştırılmaz.

Router yalnız hangi teknik yüzeylerin yükleneceğini belirler; astrolojik hüküm vermez.

## 8. Aşama 2 — Data profile

Her yüzey için durum kaydedilir:

```json
{
  "d1": "verified|partial|missing",
  "nakshatra_pada": "verified|partial|missing",
  "lords": "verified|partial|missing",
  "drishti": "verified|school_unknown|missing",
  "strength": "verified|passive|missing",
  "avastha": "verified|provisional|missing",
  "vargas": "verified|partial|missing",
  "dashas": "verified|partial|missing",
  "transits": "verified|partial|missing",
  "varshaphala": "verified|starter|missing"
}
```

Kural:

- `missing`: Katman çalışmaz.
- `partial`: Yalnız mevcut alanlar kullanılır ve sınır yazılır.
- `provisional`, `passive`, `starter`: Nihai hükmü tek başına değiştiremez.
- `school_unknown`: Yorum bloke edilir veya açık okul bilgisi istenir.

## 9. Aşama 3 — Fact inventory

Model yorumdan önce bütün kullanılabilir teknik gerçekleri normalize eder.

Her gerçek şu sözleşmeyi taşır:

```json
{
  "fact_id": "FACT-0001",
  "entity": "lagna|sun|moon|mars|mercury|jupiter|venus|saturn|rahu|ketu|house|varga|timing",
  "field": "string",
  "value": "any",
  "source_path": "string",
  "source_status": "verified|partial|provisional",
  "calculator_version": "string|null"
}
```

Fact inventory aşamasında yorum cümlesi üretilmez.

## 10. Aşama 4 — Zorunlu nakshatra/pada taraması

Tam olarak on özne denetlenir:

1. Lagna
2. Güneş
3. Ay
4. Mars
5. Merkür
6. Jüpiter
7. Venüs
8. Satürn
9. Rahu
10. Ketu

Her özne için:

```json
{
  "entity": "moon",
  "sign": "string",
  "degree": 0,
  "house": 0,
  "nakshatra": "string",
  "pada": 0,
  "nakshatra_lord": "string",
  "sign_lord": "string",
  "topic_relevance": "primary|secondary|background",
  "data_status": "verified|partial|missing"
}
```

On kayıttan biri eksikse `NAKSHATRA_SCAN` aşaması `PARTIAL` olur. Eksik özne için yorum üretilmez.

İlk taramanın zorunlu olması bütün öznelerin nihai anlatıda eşit uzunlukta yer alacağı anlamına gelmez.

## 11. Aşama 5 — Zincir grafikleri

Her özne için iki grafik oluşturulur.

### Nakshatra yöneticisi grafiği

`özne → nakshatra lordu → lordun nakshatrası → sonraki lord → tekrar/döngü`

### Burç dispozitörü grafiği

`özne → burç lordu → lordun burcu/evi → sonraki dispozitör → tekrar/döngü`

Grafik düğümü:

```json
{
  "node_id": "NODE-0001",
  "graha": "string",
  "sign": "string",
  "house": 0,
  "nakshatra": "string|null",
  "functional_roles": [],
  "strength_status": "string|null",
  "next_node_id": "string|null"
}
```

Döngüler sonsuz yürütülmez. İlk tekrar eden düğümde zincir kapanır. Aynı düğüme ulaşan farklı grafikler ortak `root_id` ile ilişkilendirilir.

## 12. Aşama 6 — D1 backbone

D1 analizi şu kartları üretir:

- Lagna kartı
- Lagna yöneticisi kartı
- Ay kartı
- Güneş kartı
- Ev/lord kartları
- Fonksiyonel rol kartları
- Ana destek ve gerilim eksenleri

Her kartın zorunlu alanları:

```json
{
  "card_id": "CARD-0001",
  "subject": "string",
  "facts": ["FACT-0001"],
  "roles": [],
  "supports": [],
  "challenges": [],
  "counterevidence": [],
  "missing_fields": [],
  "confidence": "high|medium|low|blocked"
}
```

D1 tamamlanmadan varga veya zamanlama hükmü oluşturulmaz.

## 13. Aşama 7 — Topic matrix

Her konu için bir kanıt matrisi oluşturulur:

```json
{
  "topic": "career",
  "primary_houses": [],
  "house_lords": [],
  "occupants": [],
  "drishti": [],
  "karakas": [],
  "related_houses": [],
  "nakshatra_roots": [],
  "supporting_roots": [],
  "challenging_roots": [],
  "counter_roots": []
}
```

Ev okuma sırası:

`geniş anlam alanı → ev yöneticisi → yerleşen grahalar → nakshatra/pada → nakshatra yöneticisi → dispozitör → drishti/yoga → karaka → bağlantılı evler`

Model evi tek bir klasik etikete kilitlemez. Geniş olasılık alanı yalnız teknik kanıtlarla daraltılır.

## 14. Aşama 8 — Strength layer

Rol, güç ve aktivasyon ayrı tutulur:

- **Rol:** Grahanın doğal ve fonksiyonel görevi
- **Güç:** Bu görevi ifade etme kapasitesi
- **Aktivasyon:** Belirli dönemde çalışıp çalışmadığı

Güç katmanı yalnız `verified` alanlardan hüküm üretir. `passive` veya `provisional` alanlar yardımcı not olarak kalır.

Sabit puan eşikleriyle otomatik olumlu/olumsuz hüküm kurulmaz.

## 15. Aşama 9 — Yoga ve kombinasyon doğrulaması

Her yoga veya bhanga kaydı için:

```json
{
  "combination_id": "YOGA-0001",
  "name": "string",
  "school": "string",
  "required_conditions": [],
  "met_conditions": [],
  "missing_conditions": [],
  "strength_modifiers": [],
  "cancellations": [],
  "topic_relevance": "primary|secondary|none",
  "status": "verified|partial|rejected"
}
```

`partial` veya `rejected` bir kombinasyon anlatıda gerçekleşmiş yoga gibi sunulmaz.

## 16. Aşama 10 — Varga layer

Varga yalnız intent router tarafından ilgili olarak seçilmişse yüklenir.

Her varga sonucu:

- `CONFIRM`
- `QUALIFY`
- `CHALLENGE`
- `INSUFFICIENT`

statülerinden birini alır.

Varga D1'de bulunmayan bağımsız bir vaat üretemez. Doğum saati güveni varganın hassasiyetine yetmiyorsa sonuç `INSUFFICIENT` olur.

## 17. Aşama 11 — Natal promise decision

Her ana iddia için bir hüküm nesnesi oluşturulur:

```json
{
  "judgment_id": "JDG-0001",
  "claim": "string",
  "topic": "string",
  "supporting_root_ids": [],
  "challenging_root_ids": [],
  "counter_root_ids": [],
  "varga_status": "confirm|qualify|challenge|insufficient",
  "data_limitations": [],
  "promise_status": "strong|conditional|weak|blocked|insufficient",
  "confidence": "high|medium|low|blocked"
}
```

Aynı `root_id` destek listesinde birden fazla kez sayılamaz.

Minimum hüküm kuralı:

- Güçlü hüküm için en az iki bağımsız destek kökü
- Varsa en güçlü karşı kanıtın açık kaydı
- Veri sınırlamasının güven düzeyine yansıması

## 18. Aşama 12 — Timing gate

Timing gate yalnız zaman intent'i varsa açılır.

Sıra:

1. Natal vaat
2. Mahadasha
3. Antardasha
4. Gerekirse Pratyantardasha
5. İlgili varga
6. Transit
7. Doğrulanmışsa Varshaphala

Timing nesnesi:

```json
{
  "timing_id": "TIM-0001",
  "judgment_id": "JDG-0001",
  "natal_promise_status": "conditional",
  "dasha_activation": "support|challenge|neutral|insufficient",
  "transit_activation": "support|challenge|neutral|insufficient",
  "annual_activation": "support|challenge|neutral|not_available",
  "window_start": "date|null",
  "window_end": "date|null",
  "confidence": "high|medium|low|blocked"
}
```

Natal vaat `blocked` veya `insufficient` ise model yalnız aktivasyonun gözlenen baskısını anlatabilir; vaat edilmemiş kesin sonucu üretemez.

## 19. Aşama 13 — Evidence atom sistemi

Her yorum atomu şu yapıyı taşır:

```json
{
  "evidence_id": "EVD-0001",
  "root_id": "ROOT-0001",
  "fact_ids": ["FACT-0001"],
  "statement": "string",
  "direction": "support|challenge|counter|neutral",
  "weight": "primary|secondary|context",
  "school": "string",
  "source_status": "verified|partial|provisional",
  "confidence": "high|medium|low"
}
```

Kurallar:

- Aynı teknik kökten türeyen atomlar aynı `root_id` taşır.
- `provisional` atom primary ağırlık alamaz.
- Karşı kanıt silinemez.
- Kanıt sayısı tek başına ağırlık değildir; bağımsız kök ve konu ilgisi esastır.

## 20. Aşama 14 — Technical validator

Teknik JSON anlatıdan önce şu kontrollerden geçer:

1. Zorunlu şema alanları mevcut mu?
2. On nakshatra/pada kaydı var mı?
3. Kullanılan bütün astrolojik gerçekler `fact_id` ile bağlı mı?
4. D1 omurgası tamam mı?
5. Varga hükmü D1 vaadini aşıyor mu?
6. Zamanlama natal vaat olmadan sonuç üretiyor mu?
7. Aynı `root_id` birden fazla ağırlıklandırılmış mı?
8. Tek göstergeden kesin hüküm var mı?
9. Karşı kanıt kontrol edilmiş mi?
10. Provisional katman kesin hükümde kullanılmış mı?
11. Eksik veri fallback anlatıyla örtülmüş mü?
12. Okul bilgisi belirsiz teknik kullanılmış mı?

Kritik hata varsa anlatı oluşturulmaz. Sonuç `BLOCKED_TECHNICAL_VALIDATION` olur.

## 21. Aşama 15 — Narrative renderer

Anlatı yalnız doğrulanmış teknik çekirdekten üretilir.

Sıra:

1. Net fakat koşullu ana sonuç
2. En güçlü destekleyici kanıtlar
3. Zorlayan ve karşı çıkan kanıtlar
4. Veri ve güven sınırı
5. İstenmişse zamanlama penceresi
6. Psikolojik anlam
7. Rehberlik

Anlatı katmanı `fact_id`, `evidence_id`, dosya yolu, iç validator adı veya uygulama jargonunu kullanıcıya göstermez. Ancak gerçek teknik eksik ve bunun hükme etkisi anlaşılır dille belirtilir.

## 22. Psikolojik anlam sözleşmesi

Psikolojik ifade oluşturmak için:

- En az iki bağımsız kök kanıt
- En güçlü karşı kanıt
- `high`, `medium` veya `low` güven
- Olasılık dili
- Klinik olmayan çerçeve

zorunludur.

Şablon:

`Teknik örüntü → olası içsel ihtiyaç veya gerilim → muhtemel yaşamsal görünüm → farklı çalışma olasılığı → danışanın deneyimiyle kontrol`

Model “Bu kesinlikle böyledir” yerine kanıt gücüne uygun ifade kullanır.

## 23. Rehberlik sözleşmesi

Rehberlik teknik hükmü çözüm garantisine dönüştürmez.

Her öneri:

- Küçük
- Uygulanabilir
- Düşük riskli
- Geri alınabilir
- Danışanın kontrol veya etki alanında
- Astrolojik korkuya dayanmayan

olmalıdır.

Rehberlik bölümü:

1. Kontrol edilebilir alan
2. Etki edilebilir alan
3. Kontrol dışı alan
4. Bir küçük sonraki adım

## 24. Dil ve güvenlik validatorı

Kullanıcı çıktısında aşağıdakiler reddedilir:

- Klinik tanı
- Ölüm, hastalık, ayrılık, kayıp veya başarı garantisi
- Değişmez kader ifadesi
- Korkutucu veya suçlayıcı dil
- Tek yerleşimden kişilik etiketi
- Aile üyeleri hakkında doğrulanmamış kesin biyografi
- Eksik veriyi saklayan aşırı güvenli dil
- Teknik çekirdekte bulunmayan yeni astrolojik iddia

## 25. Çıktı modları

### Short

- Ana hüküm
- En güçlü iki kanıt
- En önemli karşı/sınırlayıcı kanıt
- Güven düzeyi
- Gerekliyse tek rehberlik adımı

### Standard

- Kapsam ve veri durumu
- Nakshatra ilk tarama özeti
- D1 ve konu analizi
- Varga/güç teyidi
- Destek, zorluk ve karşı kanıt
- Zamanlama varsa pencere
- Psikolojik anlam ve rehberlik

### Deep

- Teknik JSON'un kullanıcıya uygun tam açıklaması
- On göstergelik tarama
- Zincir grafikleri özeti
- D1 kartları
- Konu matrisi
- Güç, yoga ve varga katmanları
- Natal vaat ve zamanlama
- Kanıt muhasebesi
- Psikolojik anlam ve rehberlik

Arka plan teknik kontrolleri çıktı modu kısa olsa bile atlanmaz.

## 26. Türkçe ve İngilizce üretim

Teknik çekirdek dilden bağımsızdır. Anlatı renderer'ı `request.language` alanına göre Türkçe veya İngilizce üretir.

Kurallar:

- Graha, nakshatra, pada, bhava, varga ve daşa adları sabit terminoloji sözlüğünden gelir.
- Aynı teknik statü iki dilde aynı güven düzeyini taşır.
- Çeviri yeni astrolojik yorum ekleyemez.
- Sanskrit terim ilk kullanımda açıklanabilir; sonraki kullanımlarda tutarlı biçimde korunur.

## 27. Hata ve fallback davranışı

### Eksik D1

Sonuç: `BLOCKED`. Natal analiz üretilmez.

### Eksik nakshatra/pada

Sonuç: Etkilenen özne `HOLD`; onlu tarama `PARTIAL`. Eksik özne hakkında nakshatra yorumu üretilmez.

### Eksik varga

Sonuç: Natal D1 analizi sürebilir; varga teyidi `INSUFFICIENT` olarak görünür.

### Eksik zamanlama

Sonuç: Natal vaat anlatılabilir; tarih/dönem hükmü üretilmez.

### Validator hatası

Sonuç: Kullanıcıya astrolojik fallback yazılmaz. İstek güvenli teknik hata statüsüyle durdurulur.

## 28. Minimum kabul testleri

Metodoloji uygulamaya bağlandığında en az şu testler bulunmalıdır:

1. Lagna dahil on nakshatra/pada kaydı zorunluluğu
2. Eksik bir grahada uydurma veri üretilmemesi
3. Nakshatra ve burç dispozitör zincirlerinin ayrı tutulması
4. Aynı root kanıtın çift sayılmaması
5. D1 vaadi olmadan varga hükmü kurulmaması
6. Genel natal soruda zamanlamanın otomatik açılmaması
7. Zaman sorusunda natal → daşa → transit → yıllık katman sırası
8. Karşı kanıtın çıktıda görünmesi
9. Provisional katmanın kesin hüküm üretmemesi
10. Teknik JSON'da olmayan astrolojik gerçeğin anlatıya eklenmemesi
11. Klinik, korkutucu ve kaderci dilin reddedilmesi
12. Türkçe ve İngilizce çıktıda aynı hüküm/güven düzeyinin korunması

## 29. Tamamlanma sözleşmesi

Bir çalışma ancak şu şartlarla `COMPLETE` olabilir:

- Scope ve intent belirlenmiş.
- Veri profili oluşturulmuş.
- Fact inventory tamamlanmış.
- On göstergelik nakshatra/pada taraması yapılmış.
- Nakshatra ve dispozitör grafikleri oluşturulmuş.
- D1 natal omurga tamamlanmış.
- Konu matrisi en az bir karşı kanıtla değerlendirilmiş.
- Varga ve güç katmanları doğrulama statüsüne göre kullanılmış.
- Natal vaat zamanlamadan önce sınıflandırılmış.
- Zamanlama yalnız uygun intent'te çalışmış.
- Kanıt kökleri tekilleştirilmiş.
- Teknik validator geçmiş.
- Anlatı teknik çekirdeğe sadık kalmış.
- Dil ve güvenlik validatorı geçmiş.

Bu koşullardan biri kritik düzeyde sağlanmıyorsa analiz tamamlanmış gibi gösterilmez.
