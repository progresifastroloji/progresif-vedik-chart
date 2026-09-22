# Yedi Günlük Kişisel Yorum Metodolojisi

Sürüm: digest-methodology-v8-tr-narrative-v1

Türkçe üretimde `methodologies/TURKISH_NARRATIVE.md` ortak anlatım standardı ve sunucu editör denetimi uygulanır. Tespit, konu ve alan teknik etiketi aynen kopyalanmadan doğal davranış diliyle açıklanır. Yedi gün birlikte denetlenir; bir düzeltmeden sonra da başarısızsa kişisel yorum olarak yayımlanmaz.

Bu yöntem her gün için aynı zinciri uygular: **doğrulanmış günlük gökyüzü → somut tespit → devredeki konu → yaşam alanı → yapılabilir adım → dikkat noktası**. Model hesap yapmaz, pakette olmayan bir gezegen/burç/ev/dönem çıkarmaz ve tek bir göstergeden değişmez kişilik hükmü kurmaz.

## Kanıt hiyerarşisi

Chart API aşağıdaki kanıtları üretir:

- Ay'ın o gün İstanbul saat kovasındaki doğrulanmış sidereal konumu.
- Bu konumdan hesaplanan tam Ay nakşatrası adı, pāda ve nakşatra yöneticisi. Eski `moon_nakshatra_index` alanı geriye dönük uyumluluk için tutulur; ad/pāda/lord aynı boylamdan gelir.
- Doğum Ay'ına göre günlük Ay hareketinin kişisel alanı. Bu alan yalnız doğum saati `exact` veya `approximate` ise kullanılır.
- Doğum haritası ve güncel Vimśottarī dönemi aynı anda mevcutsa dönemle desteklenen ikinci alan ve `eligible_domains` rozetleri.
- `activation`: günün konusu (`topic`), bunun sade yaşam alanı (`area`), gözlem, iki sınırlı eylem seçeneği ve dikkat noktası. Dönem kanıtı varsa `supporting_period_areas` yalnız destekleyici ikinci alanı taşır.

Doğum saati `unknown` ise ev, yükselen, ev yöneticiliği ve kişisel yaşam alanı çıkarımı kapalıdır. Bu durumda yalnız Ay'ın günlük nakşatrası ve gün ritmi anlatılır; `area` “günün ritmi” olarak kalır, kişiye ev/ilişki/iş ataması yapılmaz ve alan rozeti gönderilmez.

## Günlük kart sözleşmesi

Her kart `odak` değerini kanıttan aynen taşır ve 32–110 kelimelik tek paragraf üretir. Paragrafın sırası:

1. **Tespit:** “Ay bugün [doğrulanmış nakşatra]…”, veya veri eksikse yalnız doğrulanmış gün ritmi. Nakşatra adı, pāda veya yöneticisi pakette yoksa yazılmaz.
2. **Konu:** `activation.topic` ile günün hangi meselesinin devrede olduğu açıkça söylenir; genel “enerji yüksek/düşük” cümlesi tek başına tespit sayılmaz.
3. **Alan:** `activation.area` ile konunun hangi yaşam alanında görülebileceği belirtilir. Ev numarası kullanıcı metnine yazılmaz; sade alan adı kullanılır.
4. **Rehberlik:** `action_options` içinden en az bir gözlenebilir ve küçük adım seçilir; kullanıcıya neyi bugün yapabileceği söylenir.
5. **Sınır:** `watch_for` içinden en az bir dikkat noktası eklenir. Bu, korkutma değil, seçimi koruyan pratik sınırdır.

Bu nedenle “bir şeyler hissedebilirsin” gibi tek başına havada kalan cümleler geçerli değildir. Her paragraf okunduğunda kullanıcı şu dört sorunun cevabını görebilmelidir: **Ne gözleniyor? Hangi konu? Hangi alanda? Bugün ne yapabilirim?**

## Nakşatra dilinin sınırı

27 nakşatranın kısa temaları ve eylem tohumları `digest/nakshatra_guidance.py` içinde tutulur. Bunlar kader hükmü değil, doğrulanmış adın günlük odağa nasıl çevrileceğini sınırlayan editoryal rehberliktir. Model bu tablodaki temayı kesin sonuç gibi yazamaz; “öne çıkabilir”, “fark edebilirsin”, “değerlendirebilirsin” gibi seçim alanı bırakan dil kullanır.

Paragrafta teknik ifade yalnız pakette verilen Ay nakşatrası adıyla sınırlıdır. Model kendi başına transit, gezegen, burç, ev, yükselen, daśā veya pañcāṅga ekleyemez. Nakşatra adı yanlışsa, pakette olmayan başka bir nakşatra adı kullanılırsa veya somut kanıt hiç anılmazsa kart reddedilir.

## Alan rozetleri ve dönem

`love`, `work`, `family`, `friends` rozetleri yalnız günlük kişisel odak ile doğrulanmış dönem alanı birlikte varsa gönderilir. Rozet, paragrafta olay garantisi anlamına gelmez. Dönem yöneticisinin adı kullanıcı metnine sızdırılmaz; yalnız kanıt paketindeki tematik alanlar yazıcıya verilir.

## Derinleştir düğmesi

Derin metin aynı kanıt paketini kullanır; yeni hesap, yeni nakşatra veya yeni yaşam alanı ekleyemez. 110–140 kelimelik tek paragrafta aynı tespit–konu–alan–eylem–sınır zincirini daha fazla bağlamla açar. Premium derinleştirme yalnız mevcut gün kartının kanıtına bağlıdır.

## Güvenlik ve kalite

Kesin gelecek, garanti, korkutma, üçüncü kişinin niyeti, sağlık/hukuk/yatırım sonucu ve değişmez kişilik hükmü yasaktır. “Evren sana”, “kozmik enerji”, “şanslı gün” gibi klişeler kullanılmaz. Kanıt eksikse metin eksikliği açıkça korur; eksik veriyi genel bir cümleyle gizlemek geçerli fallback değildir.

Yalnız şu JSON döndürülür:

```json
{
  "motto": "...",
  "days": [
    {
      "date": "YYYY-MM-DD",
      "odak": "...",
      "yorum": "...",
      "alanlar": ["love", "work", "family", "friends"]
    }
  ]
}
```

Tam yedi kart döndürülür ve her tarih kanıt paketindeki tarihle birebir eşleşir.
