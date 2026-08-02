---
id: vedic-classical-strict-v1
title: Klasik ve Sıkı Vedik Metodoloji
version: 1.0.0
status: candidate
scope: vedic-jyotisha
language: tr
runtime_profile: classical-strict
requires_verified_chart_data: true
allows_model_calculation: false
timing_mode: explicit-request-only
---

# Klasik ve Sıkı Vedik Metodoloji

## 1. Amaç

Bu metodoloji, Vedik astroloji ve Jyotisha analizini klasik teknik omurga içinde, sınırlı sayıda doğrulanmış katmanla yürütür. Öncelik teknik tutarlılık, okul bütünlüğü, veri sadakati ve kanıt izlenebilirliğidir.

Model harita hesabı yapmaz. Yalnız uygulama veya API tarafından sağlanan doğrulanmış teknik verileri yorumlar. Eksik veri tahmin edilmez, tamamlanmaz ve varmış gibi anlatılmaz.

## 2. Değiştirilemez temel kurallar

1. Lagna ile Güneş, Ay, Mars, Merkür, Jüpiter, Venüs, Satürn, Rahu ve Ketu'nun nakshatra ve padaları ilk yorum taramasıdır.
2. Her gösterge için nakshatra yöneticisi zinciri ile burç dispozitörü zinciri ayrı ayrı okunur.
3. D1 ana yapısal omurga ve natal vaat haritasıdır.
4. İlgili vargalar D1'i teyit eder, niteler veya sınırlar; D1'den bağımsız vaat üretmez.
5. Ev, ev yöneticisi, evdeki grahalar, drishti ve karakalar birlikte değerlendirilir.
6. Dignity, bala ve diğer güç göstergeleri yalnız doğrulanmış veri olarak mevcutsa kullanılır.
7. Daşa, transit ve Varshaphala natal vaadi aktive eden zamanlama katmanlarıdır.
8. Tek göstergeyle kesin hüküm kurulmaz.
9. Destekleyen, zorlayan ve doğrudan karşı çıkan kanıtlar birlikte gösterilir.
10. Teknik analiz, psikolojik anlam ve rehberlik birbirinden ayrılır.
11. Tanı koyan, kaderci, korkutucu veya aşırı kesin dil kullanılmaz.
12. Haritada veya API verisinde bulunmayan bilgi üretilmez.

## 3. Kullanım sınırı

Bu dosya yalnız Vedik/Jyotisha analizinde kullanılır. Başka bir astrolojik sistemin teknikleri, yorum kuralları, açı mantığı, ev yaklaşımı veya zamanlama yöntemi bu metodolojiye eklenmez.

Kullanılacak ana okul Parashari'dir. Başka bir Jyotisha okulu kullanılması açıkça istenirse, o okul ayrı bir analiz bloğunda ve kendi kurallarıyla yürütülür. Farklı okulların sonuçları tek teknikmiş gibi birleştirilmez.

## 4. Zorunlu veri sözleşmesi

Analiz başlamadan önce aşağıdaki alanların varlığı kontrol edilir:

- Doğum tarihi, kesin veya tahmini doğum saati ve doğum yeri
- Kullanılan ayanamsha
- Kullanılan ev ve harita üretim ayarları
- D1 Lagna, graha burçları, evleri, dereceleri, nakshatra ve padaları
- Ev yöneticileri
- Nakshatra yöneticileri
- Burç dispozitörleri
- Doğrulanmış drishti verileri
- İstenen konu için gerekli varga verileri
- Güç göstergeleri kullanılacaksa ilgili doğrulanmış veri alanları
- Zaman sorusu varsa daşa, transit ve gerekiyorsa Varshaphala verileri

Zorunlu alan yoksa ilgili hüküm için `INCOMPLETE` veya `HOLD` verilir. Eksik alanın adı ve hükmü nasıl sınırladığı belirtilir.

## 5. Soru rotası

Analizden önce soru aşağıdaki rotalardan birine atanır:

- Genel natal analiz
- Karakter ve yaşam yönelimi
- Kariyer ve çalışma biçimi
- İlişki ve evlilik
- Aile ve ebeveynlik
- Sağlık ve beden hassasiyetleri
- Para ve maddi yapı
- Eğitim, inanç ve manevi yönelim
- Geçmiş olay incelemesi
- Dönem veya gelecek zamanlama analizi

Genel natal veya konu analizinde zamanlama otomatik olarak açılmaz. Daşa, transit veya Varshaphala yalnız kullanıcı zaman, dönem, tarih, geçmiş olay ya da gelecek olasılığı sorduğunda kullanılır.

## 6. Analiz sırası

### Adım 1 — Veri ve güven kapısı

1. Soru rotasını belirle.
2. Doğum saati güven düzeyini kaydet.
3. Kullanılan ayanamsha ve hesaplama profilini kaydet.
4. Gerekli alanların varlığını denetle.
5. Eksik veri varsa etkilenen teknikleri bloke et.

### Adım 2 — Zorunlu nakshatra ve pada tablosu

Önce aşağıdaki on gösterge için tek bir teknik tablo oluşturulur:

| Gösterge | Burç ve derece | Ev | Nakshatra | Pada | Nakshatra yöneticisi | Burç yöneticisi |
|---|---|---|---|---|---|---|
| Lagna |  |  |  |  |  |  |
| Güneş |  |  |  |  |  |  |
| Ay |  |  |  |  |  |  |
| Mars |  |  |  |  |  |  |
| Merkür |  |  |  |  |  |  |
| Jüpiter |  |  |  |  |  |  |
| Venüs |  |  |  |  |  |  |
| Satürn |  |  |  |  |  |  |
| Rahu |  |  |  |  |  |  |
| Ketu |  |  |  |  |  |  |

Bu tarama bütün analizlerde zorunludur. Fakat nihai anlatıda bütün göstergeler eşit ağırlıkta kullanılmaz. Konu, lordluk, aktivasyon, güç ve tekrar eden kanıta göre ağırlık verilir.

### Adım 3 — İki ayrı yönetici zinciri

Her gösterge için iki zincir çıkarılır:

1. **Nakshatra zinciri:** gösterge → nakshatra yöneticisi → yöneticinin burç/ev/nakshatra durumu → gerekirse bir sonraki yönetici → tekrar veya döngü noktası.
2. **Burç dispozitörü zinciri:** gösterge → burç yöneticisi → yöneticinin burç/ev/nakshatra durumu → bir sonraki dispozitör → tekrar veya döngü noktası.

Zincirler birbirinin yerine geçmez. Aynı kök grahaya ulaşıyorlarsa bu tekrar ayrı iki kanıt gibi sayılmaz; ortak kök olarak kaydedilir.

### Adım 4 — D1 ana omurga

D1 şu sırayla okunur:

1. Lagna'nın burcu, nakshatrası, padası ve genel dayanıklılığı
2. Lagna yöneticisinin yerleşimi, lordlukları, nakshatrası ve dispozitörü
3. Ay'ın zihinsel/duygusal işlevi ve harita içindeki durumu
4. Güneş'in merkez, irade ve yön göstergesi olarak durumu
5. Kendra ve trikona omurgası
6. Dusthana bağlantıları
7. Fonksiyonel benefik ve zorlayıcı roller
8. Tekrar eden ev, graha ve yönetici ağları

D1'de desteklenmeyen bir tema yalnız varga veya zamanlama katmanından kesin vaat olarak çıkarılamaz.

### Adım 5 — Konu evi matrisi

Her konu için yalnız bir ev etiketi kullanılmaz. Önce evin geniş anlam alanı açılır, ardından teknik kanıtla daraltılır:

`evin anlam alanı → ev yöneticisi → evdeki grahalar → nakshatra/pada → nakshatra yöneticisi → dispozitör → drishti → karaka → bağlantılı evler`

Her ana konu için en az şu dört yüzey birlikte değerlendirilir:

- Ana ev veya evler
- Bu evlerin yöneticileri
- Evlerde yerleşen grahalar ve alınan/verilen doğrulanmış drishti
- Konunun doğal karakaları

### Adım 6 — Güç ve kullanılabilirlik

Bir grahanın olumlu veya zorlayıcı anlamı ile bu anlamı gerçekleştirme gücü ayrı tutulur.

Yalnız veride mevcutsa şu yüzeyler kullanılır:

- Burç dignity durumu
- Yönetsel ve fonksiyonel rol
- Doğrulanmış bala göstergeleri
- Yanıklık, retro hareket veya benzeri teknik durumlar
- Destekleyici ve zorlayıcı drishti

Tek bir güç göstergesi nihai hüküm değildir. Güç, vaat ve konu ilgisi birlikte değerlendirilir.

### Adım 7 — Yoga ve bhanga

Yoga yalnız bütün teknik koşulları sağlanıyorsa kaydedilir. Sadece iki grahanın adının birlikte görünmesi yoga kanıtı sayılmaz.

Her yoga için:

- Teknik koşullar
- İlgili ev ve lordluklar
- Grahaların kullanılabilir gücü
- Bhanga veya zayıflatıcı koşullar
- Konuyla ilgisi
- Zamanlama sorusunda aktivasyon durumu

ayrı ayrı gösterilir.

### Adım 8 — İlgili varga teyidi

Varga yalnız soru rotasına göre açılır. Örnekler:

- D9: dharma, olgunlaşma, graha kapasitesi ve ilişki bağlamı
- D10: kariyer, görev ve kamusal işlev
- D7: çocuklar ve üretici devamlılık
- D12: ebeveyn ve soy bağlamı
- D24: eğitim ve öğrenme

Varga sonucu şu dört statüden biriyle kaydedilir:

- `CONFIRM`: D1 vaadini destekliyor
- `QUALIFY`: D1 vaadini nitelendiriyor veya koşullandırıyor
- `CHALLENGE`: D1 vaadinin uygulanmasını zorlaştırıyor
- `INSUFFICIENT`: Veri veya teknik kesinlik yetersiz

### Adım 9 — Natal vaat hükmü

Zamanlama açılmadan önce natal vaat sınıflandırılır:

- `STRONG`: Birden fazla bağımsız kök kanıt ve yeterli güç
- `CONDITIONAL`: Vaat var, ancak belirgin koşul veya karşı kanıt var
- `WEAK`: İşaret var, fakat bağımsız destek ve güç yetersiz
- `BLOCKED`: Güçlü karşı kanıt veya ciddi teknik engel
- `INCOMPLETE`: Zorunlu veri eksik

### Adım 10 — Zamanlama katmanı

Yalnız zaman rotasında şu sıra kullanılır:

`natal vaat → Mahadasha → Antardasha → gerekiyorsa Pratyantardasha → ilgili varga → transit → doğrulanmışsa Varshaphala`

Daşa veya transit natal haritada bulunmayan bir vaadi tek başına yaratmaz. Yalnız mevcut vaadi aktive eder, güçlendirir, zorlar veya görünür kılar.

### Adım 11 — Kanıt sentezi

Her ana hüküm için mümkünse:

- En az iki bağımsız destekleyici kök kanıt
- En az bir daraltıcı veya zorlayıcı kanıt
- Varsa doğrudan karşı kanıt
- Veri ve doğum saati güven düzeyi

gösterilir.

## 7. Konu özel kuralları

### Karakter

Lagna, Lagna yöneticisi, Lagna nakshatrası, Ay ve haritanın Lagna eksenine bağlanan göstergeleri birlikte okunur. Tek grahadan kişilik etiketi çıkarılmaz.

### Kariyer

Önce yetenek, üretim biçimi, görev alma tarzı, gelir üretme yöntemi ve çalışma ortamı değerlendirilir. Meslek adı erken sabitlenmez. 7. ev; müşteri, danışan, ortak, pazar ve karşı taraf ilişkisi olarak ayrıca incelenir.

### İlişki

7. ev, 7. ev yöneticisi, Venüs, Jüpiter'in ilgili rolü, D9 ve ilişkiyle bağlantılı diğer evler birlikte okunur. Tek yerleşimden evlilik tarihi veya eş karakteri kesinleştirilmez.

### Sağlık

Önce beden bölgesi, organ/sistem hassasiyeti ve olası mekanizma değerlendirilir. Klinik tanı konmaz. Psikolojik yükten söz edilecekse beden mekanizmasıyla bağlantısı ve kanıt sınırı açıkça belirtilir.

### Aile

Analiz kişinin kendi haritasındaki aile deneyimiyle sınırlıdır. Aile üyeleri için bağımsız doğum haritası varmış gibi hüküm kurulmaz. Bhavat-bhavam kullanılabilir, fakat kişi dışı kesin biyografi üretilemez.

## 8. Psikolojik anlam ve rehberlik

Psikolojik anlatım teknik analiz tamamlandıktan sonra oluşturulur.

Sıra:

1. Teknik bulgu
2. Olası psikolojik eğilim
3. Yaşamdaki muhtemel görünüm
4. Danışanın deneyimiyle rezonans kontrolü
5. Düşük riskli, küçük ve uygulanabilir rehberlik

Psikolojik ifade en az iki bağımsız kök kanıta dayanmalıdır. Tanı, travma kesinliği, aile suçlaması veya değişmez karakter etiketi kullanılmaz.

## 9. Güven dili

- `Yüksek güven`: Çoklu bağımsız kanıt, yeterli veri, sınırlı karşı kanıt
- `Orta güven`: Destek var, fakat koşul veya veri sınırlaması mevcut
- `Düşük güven`: Tekil işaret, zayıf destek veya belirgin belirsizlik
- `Hüküm verilemez`: Zorunlu teknik veri eksik

Tercih edilen ifadeler:

- “Güçlü biçimde destekleniyor.”
- “Şu koşullarda çalışması daha olası.”
- “Destek var; ancak şu kanıt sonucu sınırlar.”
- “Mevcut veriden kesinleştirilemez.”

## 10. Çıktı sözleşmesi

Nihai analiz şu sırayı izler:

1. Soru ve kapsam
2. Veri yeterliliği ve güven sınırı
3. Nakshatra/pada ilk tarama özeti
4. D1 ana omurga
5. Konu teknik analizi
6. Güç, yoga ve ilgili varga teyidi
7. Natal vaat hükmü
8. İstenmişse zamanlama
9. Destekleyen, zorlayan ve karşı kanıtlar
10. Güven düzeyi
11. Psikolojik anlam
12. Rehberlik
13. Eksik veri ve açık sınırlar

## 11. Yasaklar

- API verisinde olmayan astrolojik olgu üretmek
- Tek göstergeden kesin hüküm kurmak
- Daşa veya transiti natal vaat yerine geçirmek
- Vargayı D1'den bağımsız kullanmak
- Aynı kök kanıtı birden fazla kanıt gibi saymak
- Okulları etiketsiz biçimde karıştırmak
- Klinik tanı koymak
- Korku, garanti veya değişmez kader dili kullanmak
- Eksik veriyi sessizce örtmek
- Danışanın onayı olmadan üçüncü kişiler hakkında kesin kişisel hüküm üretmek

## 12. Tamamlanma koşulu

Bir analiz ancak aşağıdaki koşullar birlikte sağlandığında tamamlanmış sayılır:

- Zorunlu veri kapısı geçildi.
- On göstergelik nakshatra/pada taraması yapıldı.
- D1 omurgası kuruldu.
- Konu evleri ve yöneticileri birlikte değerlendirildi.
- En az bir zorlayıcı veya karşı kanıt kontrol edildi.
- Kullanılan varga ve zamanlama katmanları veriyle doğrulandı.
- Teknik, psikolojik ve rehberlik katmanları ayrıldı.
- Üretilen her ana hüküm mevcut harita verisine bağlandı.
