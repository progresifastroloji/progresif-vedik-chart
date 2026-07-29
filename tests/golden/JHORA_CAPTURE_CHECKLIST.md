# JHora Capture Checklist

Bu dosya, `fixtures.json` icindeki chartlar icin Jagannatha Hora ciktisini
bagimsiz ikinci kontrol olarak toplama kontrol listesidir.

JHora degerleri eklenmeden once Swiss referanslar zaten uretilmis olabilir, ama
`expected` degerleri final golden kabul edilmez. JHora uyumu veya fark notu
gereklidir.

## Genel Ayarlar

Her chart icin JHora'da su ayarlar kontrol edilmelidir:

- Ayanamsa: Lahiri
- Zodiac: sidereal
- Nodes: true node / true Rahu
- Birth time: fixture icindeki yerel saat
- Timezone/UTC offset: fixture icindeki deger
- Latitude/longitude: fixture icindeki koordinatlar
- Daylight saving: fixture tarihiyle uyumlu
- Chart reference: D1/Rasi
- Bhava Chalit / Sripati: JHora'da kullanilan bhava/cusp sistemi acikca not
  edilmeli. Sripati yoksa kullanilan alternatif ev sistemi fark notuna
  yazilmali.

## Chart A

Fixture:

- ID: `chart_a`
- Date: `2000-01-15`
- Time: `12:00`
- Timezone: `Europe/London`
- UTC offset: `+00:00`
- Place: `London, United Kingdom`
- Latitude: `51.5074`
- Longitude: `-0.1278`

Toplanacak alanlar:

- D1 Lagna burcu ve derece
- D1 gezegen burcu ve derece: Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn,
  Rahu, Ketu
- Ay nakshatra ve pada
- Vimshottari dogum ani aktif maha/antara/pratyantar
- Chara Dasha dogum ani aktif maha/antara; kullanilan Chara variant/ayar notu
- Yogini Dasha dogum ani aktif maha/antara/pratyantar; kullanilan Yogini
  variant/ayar notu
- Bhava Chalit / Sripati cusp tablosu: 12 ev cusp burcu/derecesi,
  baslangic/bitis araligi varsa
- Bhava Chalit gezegen ev atamalari: Whole Sign ev, Bhava Chalit ev, ev
  degisti bayragi
- D9 gezegen burclari
- D10 gezegen burclari
- D7 gezegen burclari

Kayit dosyasi:

- `references/chart_a_jhora.txt`

## Chart B

Fixture:

- ID: `chart_b`
- Date: `2015-01-15`
- Time: `12:00`
- Timezone: `Europe/Istanbul`
- UTC offset: `+02:00`
- Place: `Istanbul, Turkey`
- Latitude: `41.0082`
- Longitude: `28.9784`

Toplanacak alanlar:

- D1 Lagna burcu ve derece
- D1 gezegen burcu ve derece: Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn,
  Rahu, Ketu
- Ay nakshatra ve pada
- Timezone/DST ayar notu
- Vimshottari dogum ani aktif maha/antara/pratyantar
- Chara Dasha dogum ani aktif maha/antara; kullanilan Chara variant/ayar notu
- Yogini Dasha dogum ani aktif maha/antara/pratyantar; kullanilan Yogini
  variant/ayar notu
- Bhava Chalit / Sripati cusp tablosu: 12 ev cusp burcu/derecesi,
  baslangic/bitis araligi varsa
- Bhava Chalit gezegen ev atamalari: Whole Sign ev, Bhava Chalit ev, ev
  degisti bayragi
- D9 gezegen burclari
- D10 gezegen burclari
- D7 gezegen burclari

Kayit dosyasi:

- `references/chart_b_jhora.txt`

## Chart C

Fixture:

- ID: `chart_c`
- Date: `1961-08-04`
- Time: `19:24`
- Timezone: `Pacific/Honolulu`
- UTC offset: `-10:00`
- Place: `Honolulu, Hawaii, United States`
- Latitude: `21.3069`
- Longitude: `-157.8583`
- Source note: public birth certificate time; coordinates use Honolulu city
  coordinates, not hospital-level coordinates.

Toplanacak alanlar:

- D1 Lagna burcu ve derece
- D1 gezegen burcu ve derece: Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn,
  Rahu, Ketu
- Ay nakshatra ve pada
- Vimshottari dogum ani aktif maha/antara/pratyantar
- Chara Dasha dogum ani aktif maha/antara; kullanilan Chara variant/ayar notu
- Yogini Dasha dogum ani aktif maha/antara/pratyantar; kullanilan Yogini
  variant/ayar notu
- Bhava Chalit / Sripati cusp tablosu: 12 ev cusp burcu/derecesi,
  baslangic/bitis araligi varsa
- Bhava Chalit gezegen ev atamalari: Whole Sign ev, Bhava Chalit ev, ev
  degisti bayragi
- D9 gezegen burclari
- D10 gezegen burclari
- D7 gezegen burclari

Kayit dosyasi:

- `references/chart_c_jhora.txt`

## Fark Notu Standardi

JHora ve Swiss referanslari farkliysa su sirayla kontrol edilir:

1. Dogum tarihi ve yerel saat ayni mi?
2. Timezone ve DST ayari ayni mi?
3. Lahiri ayanamsa ayni mi?
4. True Rahu mu kullaniliyor?
5. Koordinatlar ayni mi?
6. JHora derece formati burc ici derece mi, toplam longitude mu?
7. Bhava Chalit icin JHora'daki ev sistemi Sripati mi, baska cusp sistemi mi?
8. Cusp farki tolerans disinda mi?
9. Gezegen farki tolerans disinda mi?

Fark devam ederse ilgili `chart_*_jhora.txt` dosyasina su blok eklenir:

```text
## Difference Notes

- Field:
- Swiss value:
- JHora value:
- Difference:
- Likely cause:
- Decision:
```

## Fixture Guncelleme Kurali

- JHora ciktisi ham olarak ilgili `references/chart_*_jhora.txt` dosyasina
  eklenmeden `fixtures.json expected` degerleri final sayilmaz.
- JHora Swiss ile uyumluysa `expected.source_status` daha sonra
  `swiss_and_jhora_matched` yapilabilir.
- Fark varsa `expected.source_status` `source_discrepancy_pending_review`
  olmalidir.
- Vimshottari ve varga alanlari ancak JHora ciktisi alindiktan sonra
  doldurulmalidir.
- Bhava Chalit alanlari JHora cusp sistemi netlesmeden ve Swiss ile fark notu
  yazilmadan doldurulmaz.
