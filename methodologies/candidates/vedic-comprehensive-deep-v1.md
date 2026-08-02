---
id: vedic-comprehensive-deep-v1
title: Geniş ve Derin Vedik Metodoloji
version: 1.0.0
status: candidate
scope: vedic-jyotisha
language: tr
runtime_profile: comprehensive-deep
requires_verified_chart_data: true
allows_model_calculation: false
timing_mode: route-gated
advanced_layers: validation-gated
---

# Geniş ve Derin Vedik Metodoloji

## 1. Amaç

Bu metodoloji, Vedik/Jyotisha analizinin klasik çekirdeğini korurken nakshatra, dispozitör, bhava, varga, bala, avastha, yoga, daşa, transit ve yıllık zamanlama katmanlarını kapsamlı bir kanıt sistemi içinde birleştirir.

Amaç çok sayıda teknik sıralamak değil, aynı yaşam temasının farklı katmanlarda nasıl desteklendiğini, zorlandığını veya koşullandığını göstermektir. Hiçbir katman tek başına nihai hüküm değildir.

Model hesaplama yapmaz. Uygulama veya API'nin sunmadığı veri üretilmez. Gelişmiş bir katman ancak veri, okul, hesaplama yöntemi ve doğrulama durumu biliniyorsa açılır.

## 2. Değiştirilemez temel kurallar

1. Lagna ve dokuz grahanın nakshatra/padaları bütün analizlerde ilk yorum taramasıdır.
2. Nakshatra yöneticisi ve burç dispozitörü zincirleri ayrı kanıt ağlarıdır.
3. D1 natal vaat ve bütün analizlerin ana omurgasıdır.
4. Vargalar yalnız D1 vaadini teyit eder, niteler, yönlendirir veya sınırlar.
5. Ev, ev yöneticisi, yerleşen grahalar, drishti, karaka ve bağlantılı evler birlikte okunur.
6. Güç, rol ve aktivasyon birbirinden ayrılır.
7. Daşa, transit ve Varshaphala yalnız natal vaadin zaman içindeki aktivasyonunu gösterir.
8. Aynı kök kanıt farklı tekniklerde tekrar görünse bile bir kez ağırlıklandırılır.
9. Destek, zorluk, karşı kanıt ve belirsizlik birlikte raporlanır.
10. Teknik analiz tamamlanmadan psikolojik anlatı veya rehberlik üretilmez.
11. Veri yoksa ilgili katman `INCOMPLETE`, doğrulama yoksa `PROVISIONAL` olur.
12. Tanı, korkutma, garanti ve değişmez kader dili yasaktır.

## 3. Katman modeli

Metodoloji dokuz katmandan oluşur:

1. **Veri ve doğrulama katmanı**
2. **Nakshatra/pada ilk tarama katmanı**
3. **D1 natal omurga katmanı**
4. **Konu ve kanıt ağı katmanı**
5. **Güç, hal ve yoga katmanı**
6. **Varga teyit ve derinleştirme katmanı**
7. **Natal vaat ve karşı kanıt katmanı**
8. **Zamanlama ve aktivasyon katmanı**
9. **Psikolojik anlam, rehberlik ve anlatı katmanı**

Katmanlar bu sırayla çalışır. Sonraki katman önceki katmanın eksik bıraktığı astrolojik gerçeği uydurarak tamamlayamaz.

## 4. Veri ve doğrulama profili

Her analiz için bir `validation_profile` oluşturulur:

| Alan | Olası durum |
|---|---|
| Doğum saati | exact / approximate / uncertain / unknown |
| Ayanamsha | verified / declared / unknown |
| D1 | verified / incomplete |
| Nakshatra ve pada | verified / incomplete |
| Drishti | verified / school-unknown / incomplete |
| Varga | verified / partial / unavailable |
| Bala | verified / passive / unavailable |
| Avastha | verified / provisional / unavailable |
| Yoga | verified-conditions / partial-conditions |
| Daşa | verified / partial / unavailable |
| Transit | verified-date / unavailable |
| Varshaphala | verified / starter / unavailable |

`provisional`, `passive`, `starter` veya `school-unknown` durumundaki veri nihai hükmü tek başına değiştiremez.

## 5. Soru rotası ve zorunlu yüzeyler

### Genel natal

Zorunlu: D1, on nakshatra/pada, yönetici zincirleri, Lagna omurgası, Ay, Güneş, ev-lord ağları, temel güç ve karşı kanıt.

### Karakter

Zorunlu: Lagna, Lagna yöneticisi, Lagna nakshatrası/padası, Ay, Güneş, 1. ev bağlantıları ve D9 teyidi mevcutsa graha olgunlaşması.

### Kariyer

Zorunlu: 10., 2., 6., 7. ve 11. ev ağları; ilgili lordlar; Satürn, Güneş, Merkür ve Jüpiter'in haritadaki fonksiyonel rolleri; D10. Önce çalışma/üretim biçimi, sonra mesleki yönelim değerlendirilir.

### İlişki

Zorunlu: 7. ev ve yöneticisi, Venüs, Jüpiter'in ilgili rolü, 2. ve 8. ev bağları, D9. İlişki kapasitesi, eşleşme biçimi ve zamanlama ayrı başlıklardır.

### Aile ve ebeveynlik

Zorunlu: 2., 4., 9., 3. ve 11. evlerden soruyla ilgili olanlar; Ay, Güneş ve ilgili karakalar; gerekirse D12. Analiz kişinin deneyimiyle sınırlıdır.

### Sağlık

Zorunlu: Lagna, Lagna yöneticisi, 1., 6., 8. ve 12. ev ağları; Güneş, Ay ve konuya bağlı grahalar; güç ve zorlanma kanıtları. Önce beden bölgesi ve mekanizma adayı değerlendirilir. Tanı üretilmez.

### Eğitim ve manevi yönelim

Zorunlu: 4., 5., 9. ve 12. ev ağları; Merkür, Jüpiter, Ay; gerekiyorsa D24 ve D20.

### Zaman veya olay

Zorunlu: Önce ilgili natal vaat; sonra daşa zinciri, ilgili varga, transit ve doğrulanmışsa yıllık harita.

## 6. Ayrıntılı analiz akışı

### Aşama 1 — Fakt tabanı

Harita verisi yorum yapılmadan listelenir. Burç, derece, ev, nakshatra, pada, lordluk, drishti ve varga verilerinin kaynağı korunur.

Her teknik gerçek benzersiz bir `fact_id` alır. Aynı veri farklı dosyalarda tekrar ediyorsa yeni gerçek sayılmaz.

### Aşama 2 — On göstergelik nakshatra/pada taraması

Lagna ve dokuz graha için:

- Burç ve derece
- Ev
- Nakshatra ve pada
- Nakshatra yöneticisi
- Nakshatra yöneticisinin D1 yerleşimi
- Burç dispozitörü
- Konu ilgisi
- İlk destek/zorluk yönü

kaydedilir.

Bu tarama zorunludur. Fakat yalnız konu taşıyıcıları, Lagna ekseni, aktif daşa lordları ve tekrar eden kök grahalar uzun anlatıya taşınır.

### Aşama 3 — Nakshatra yönetici grafiği

Her gösterge için zincir:

`gösterge → nakshatra yöneticisi → yöneticinin nakshatrası → bir sonraki yönetici → döngü veya son kullanılabilir veri`

Zincirin nihai grahası otomatik “sonuç yöneticisi” değildir. Bütün ara grahaların ev, lordluk, güç ve konu ilgisi birlikte değerlendirilir.

### Aşama 4 — Burç dispozitör grafiği

Her gösterge için:

`gösterge → burç yöneticisi → yöneticinin burcu ve evi → bir sonraki dispozitör → döngü`

Karşılıklı ağırlama, kendi burcunda sonlanma veya tekrar eden graha varsa ayrı teknik durum olarak kaydedilir. Bu durumun etkisi tek başına olumlu veya olumsuz sayılmaz.

### Aşama 5 — D1 natal omurga

1. Lagna ve Lagna yöneticisi
2. Ay ve zihinsel işleyiş
3. Güneş ve merkez yön
4. Kendra ve trikona ağı
5. Dusthana ve işlevsel zorluklar
6. Fonksiyonel lordluklar
7. Tekrar eden graha/ev/nakshatra kökleri
8. Haritanın genel vaat ve gerilim eksenleri

Bu aşamanın sonunda zamanlamadan bağımsız bir natal özet oluşturulur.

### Aşama 6 — Geniş ev anlamı ve teknik daraltma

Bir ev tek anahtar kelimeye kapatılmaz. Önce geniş olasılık kümesi görülür; sonra şu zincirle daraltılır:

`ev → ev yöneticisi → evdeki grahalar → nakshatra/pada → nakshatra yöneticisi → dispozitör → drishti/yoga → karakalar → bağlantılı evler`

Zaman sorusu yoksa bu zincire daşa veya transit otomatik eklenmez.

### Aşama 7 — Rol, güç ve aktivasyon ayrımı

Her önemli graha için üç ayrı kart oluşturulur:

1. **Rol kartı:** doğal anlamlar, fonksiyonel lordluklar, konu görevi
2. **Güç kartı:** dignity, bala, avastha, destek ve hasar
3. **Aktivasyon kartı:** daşa, transit veya yıllık zamanlamada aktif olup olmadığı

Güçlü bir graha her zaman kolay sonuç üretmez; zorlayıcı işlevini güçlü biçimde çalıştırabilir. Zayıf bir graha da olumlu vaadi gerçekleştirmekte zorlanabilir.

### Aşama 8 — Bala ve avastha

Yalnız doğrulanmış veri alanları kullanılır. Bala aileleri birbirine karıştırılmaz ve aynı kök ölçüm iki kez sayılmaz.

Kullanım ilkeleri:

- Bala, grahanın ifade kapasitesini değiştirir; anlamını tek başına değiştirmez.
- Avastha, grahanın işleyiş tarzını niteler; tek başına olay üretmez.
- Passive veya provisional statülü ölçümler yalnız dipnot niteliğinde kalır.
- Rahu ve Ketu için hesaplama profili açık değilse sayısal güç hükmü kurulmaz.

### Aşama 9 — Yoga, bhanga ve arishta ağı

Her kombinasyon için:

- Tam teknik koşul
- Hangi okul tanımıyla kullanıldığı
- İlgili lordluk ve evler
- Güç ve zarar koşulları
- Bhanga veya karşı etki
- Konu ilgisi
- Zamanlama aktivasyonu

kaydedilir.

Yoga adı tek başına sonuç değildir. Yoga sonucu ancak natal yapı, güç ve aktivasyon birlikte destekliyorsa anlatıya taşınır.

### Aşama 10 — Varga matrisi

Soruya ilgili bütün doğrulanmış vargalar tek bir matriste değerlendirilir:

| Varga | İncelenen konu | D1 ile ilişki | Sonuç | Veri durumu |
|---|---|---|---|---|
| D9 | Olgunlaşma/dharma/ilişki | confirm/qualify/challenge |  |  |
| D10 | Kariyer/görev | confirm/qualify/challenge |  |  |
| İlgili diğer varga | Konuya göre | confirm/qualify/challenge |  |  |

Doğum saati hassasiyeti yüksek vargalarda güven seviyesi ayrıca düşürülür.

### Aşama 11 — Ayrı okul teyidi

Parashari dışındaki bir Jyotisha yaklaşımı kullanılacaksa:

- Açıkça etiketlenir.
- Kendi hesaplama ve yorum kurallarıyla yürütülür.
- Parashari kanıt atomlarıyla aynı kök kimlik altında birleştirilmez.
- Sonuç yalnız destekleyici, zorlayıcı veya ayrışan teyit olarak gösterilir.

### Aşama 12 — Natal vaat sınıflaması

Her ana iddia şu yüzeylerle test edilir:

- D1 desteği
- Nakshatra/dispozitör desteği
- Ev/lord/karaka desteği
- Güç ve kullanılabilirlik
- Varga teyidi
- Yoga veya bhanga etkisi
- Doğrudan karşı kanıt

Sonuç:

- `STRONG_PROMISE`
- `CONDITIONAL_PROMISE`
- `WEAK_PROMISE`
- `BLOCKED_PROMISE`
- `INSUFFICIENT_DATA`

### Aşama 13 — Zamanlama

Zamanlama yalnız ilgili rota seçildiğinde açılır:

1. Natal vaadin varlığı
2. Mahadasha lordunun natal rolü
3. Antardasha lordunun rolü ve MD lorduyla ilişkisi
4. Gerekirse Pratyantardasha
5. İlgili vargada dönem lordlarının durumu
6. Transitlerin natal vaat ve daşa lordlarıyla teması
7. Doğrulanmışsa Varshaphala/Tajika katmanı
8. Sonuç penceresi ve güven düzeyi

Zamanlama sonucu kesin tarih garantisi değil, etkinleşme penceresi ve olasılık ağırlığı olarak verilir.

### Aşama 14 — Kök neden, tezahür ve tetikleyici

Her önemli sonuç üçe ayrılır:

- **Kök neden:** Natal haritadaki temel vaat veya gerilim
- **Tezahür:** Konunun yaşamda aldığı muhtemel biçim
- **Tetikleyici:** Daşa, transit veya yıllık haritanın etkinleştirici rolü

Tetikleyici kök neden gibi anlatılmaz.

### Aşama 15 — Kanıt muhasebesi

Her ana hüküm için:

| Alan | Açıklama |
|---|---|
| Destekleyen kök kanıtlar | Bağımsız teknik kökler |
| Zorlayan kanıtlar | Vaadi koşullandıran etkenler |
| Karşı kanıtlar | Hükmün tersini doğrudan destekleyen etkenler |
| Tekrarlar | Aynı kökün farklı görünüşleri |
| Eksik yüzeyler | Hükmü sınırlandıran veri eksikleri |
| Güven | high / medium / low / blocked |

## 7. Gelişmiş katman açma kuralları

Bir gelişmiş teknik yalnız aşağıdaki dört koşul birlikte sağlanırsa kullanılabilir:

1. İlgili veri API veya teknik pakette mevcut.
2. Hesaplama yöntemi ve okul profili belli.
3. En az bir doğrulama veya golden kontrol statüsü mevcut.
4. Teknik soru rotasıyla doğrudan ilgili.

Bu kapı özellikle şu katmanlar için zorunludur:

- Ayrıntılı avastha aileleri
- Vimshopaka Bala
- Ashtakavarga
- İleri düzey yoga/bhanga katalogları
- Hassas vargalar
- Varshaphala, Tajika ve Saham
- Rektifikasyon destekleri
- Upagraha yüzeyleri

## 8. Psikolojik anlam katmanı

Psikolojik anlam teknik hükmün çevirisidir; ayrı bir astrolojik hesaplama değildir.

Her psikolojik ifade şu koşulları taşımalıdır:

- En az iki bağımsız kök kanıt
- Varsa karşı kanıt
- Olasılık dili
- Danışanın yaşam deneyimiyle doğrulama payı
- Klinik olmayan ifade

Şablon:

`Teknik bulgu → olası içsel eğilim → muhtemel davranış örüntüsü → farklı çalışma ihtimali → rezonans sorusu`

## 9. Rehberlik katmanı

Rehberlik üç alana ayrılır:

1. **Kontrol alanı:** Kişinin doğrudan değiştirebileceği küçük davranışlar
2. **Etki alanı:** İletişim, planlama ve destekle iyileştirilebilecek koşullar
3. **Kontrol dışı alan:** Kabul, sınır ve destek gerektiren koşullar

Öneriler küçük, uygulanabilir, düşük riskli ve geri alınabilir olmalıdır. Korku temelli remedy, garanti veya ticari baskı kullanılmaz.

## 10. Çıktı formatı

1. Kapsam ve soru rotası
2. Veri/validation profili
3. On göstergelik nakshatra/pada tablosu
4. Nakshatra ve dispozitör zincirlerinin özeti
5. D1 natal omurga
6. Konu kanıt matrisi
7. Rol, güç ve aktivasyon kartları
8. Yoga/bhanga değerlendirmesi
9. Varga matrisi
10. Natal vaat sınıflaması
11. İstenmişse zamanlama pencereleri
12. Kök neden/tezahür/tetikleyici ayrımı
13. Destek, zorluk ve karşı kanıt
14. Güven düzeyi ve eksikler
15. Psikolojik anlam
16. Rehberlik

## 11. Kısa yanıt modu

Kısa yanıt istenirse bütün teknik kontroller arka planda yine yapılır. Kullanıcıya yalnız şu özet gösterilir:

1. Net sonuç
2. En güçlü iki bağımsız kanıt
3. En önemli sınırlayıcı veya karşı kanıt
4. Güven düzeyi
5. Gerekliyse küçük rehberlik

On göstergelik ilk tarama atlanmaz; yalnız tamamı anlatıya dökülmez.

## 12. Yasaklar

- Eksik teknik yüzeyi varsaymak
- Farklı okulları tek hesap gibi birleştirmek
- Aynı kök kanıtı tekrar tekrar ağırlıklandırmak
- Vargadan bağımsız natal vaat üretmek
- Daşa veya transit ile natal vaadi değiştirmek
- Provisional katmanı kesin kanıt gibi kullanmak
- Yoga adından otomatik sonuç üretmek
- Tek göstergeden psikolojik, mesleki veya ilişkisel kesinlik üretmek
- Klinik tanı, korku veya değişmez kader dili kullanmak
- Doğum saati belirsizliğini gizlemek

## 13. Tamamlanma koşulu

Analiz ancak şu kontroller geçerse tamamlanır:

- Zorunlu veri yüzeyleri mevcut veya eksikler açıkça bloke edilmiş.
- On nakshatra/pada taraması tamamlanmış.
- İki yönetici zinciri çıkarılmış.
- D1 natal vaat oluşturulmuş.
- Konu kanıt ağı ve en az bir karşı kanıt denetlenmiş.
- Gelişmiş katmanlar validation gate'ten geçmiş.
- Aynı kök kanıtlar tekilleştirilmiş.
- Zamanlama yalnız natal vaat üzerine kurulmuş.
- Teknik, psikolojik ve rehberlik katmanları ayrılmış.
- Nihai güven düzeyi veri ve kanıt durumuyla uyumlu.
