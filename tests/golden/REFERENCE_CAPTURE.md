# Golden Reference Capture Method

Bu dosya, golden fixture degerleri doldurulmadan once dis referans ciktisinin
nasil alinacagini tarif eder.

Bu asamada otomatik test yoktur. Bu dosya bir calistirma plani ve manuel kontrol
standardidir.

## Genel Kural

1. Once ham referans ciktisi `references/` altindaki ilgili dosyaya eklenir.
2. Kaynak ayarlari dosyada acikca yazili olmalidir.
3. Ancak bundan sonra `fixtures.json` icindeki `expected` alanlari doldurulur.
4. Iki kaynak uyusmuyorsa `expected` degeri yazmadan once fark notu eklenir.

## Swiss Ephemeris / swetest

Yerel makinede `swetest` varsa D1 gezegen boylamlari icin kullanilabilir.
Bu ortamda su an `swetest` bulunamadi; bu nedenle kurulum veya yeni arac ekleme
ayri onay gerektirir.

### Ayarlar

- Ayanamsa: Lahiri
- Coordinate system: sidereal zodiac
- Node: true node / true Rahu
- Time input: UTC
- Longitude convention: east positive, west negative

### Fixture Zaman Donusumu

| Fixture | Yerel saat | Timezone | UTC saat |
| --- | --- | --- | --- |
| chart_a | 2000-01-15 12:00 | Europe/London | 2000-01-15 12:00 |
| chart_b | 2015-01-15 12:00 | Europe/Istanbul | 2015-01-15 10:00 |
| chart_c | 1961-08-04 19:24 | Pacific/Honolulu | 1961-08-05 05:24 |

### Ornek swetest Komutlari

Bu komutlar yalnizca referans uretmek icindir; proje kodunu degistirmez.

```bash
# chart_a
swetest -b15.01.2000 -ut12:00 -sid1 -p0123456789 -fPlsZ -g, -head

# chart_b
swetest -b15.01.2015 -ut10:00 -sid1 -p0123456789 -fPlsZ -g, -head

# chart_c
swetest -b05.08.1961 -ut05:24 -sid1 -p0123456789 -fPlsZ -g, -head
```

Kontrol notu:
- `-sid1` Lahiri ayanamsa icin kullanilir.
- `-ut` UTC saati ister; yerel saat dogrudan girilmez.
- Komut ciktisi once `references/chart_*_swiss_ephemeris.txt` dosyasina
  ham olarak eklenmelidir.

## Jagannatha Hora

JHora ciktisi manuel ikinci kaynak olarak kullanilir.

### Manuel Ayarlar

- Ayanamsa: Lahiri
- Nodes: true node / true Rahu
- Chart style: Vedic / sidereal
- Birth time: yerel saat
- Timezone: fixture icindeki timezone ve offset ile ayni
- Coordinates: fixture icindeki enlem/boylam

### Aktarilacak Alanlar

Ilk turda JHora'dan su alanlar alinmalidir:

- Lagna burcu ve derecesi
- D1 gezegen burclari ve dereceleri
- Ay nakshatra ve pada
- Vimshottari dogum ani aktif dasha zinciri
- D9, D10, D7 gezegen burclari

JHora ciktisi once `references/chart_*_jhora.txt` dosyasina ham olarak
eklenmelidir.

## Varshaphala / Tajika

Varshaphala/Tajika referansi, yeni rektifikasyon agirligi eklemek icin degil,
yillik katmanlarin dis kaynakla ne kadar uyumlu oldugunu yakalamak icindir.

Ilk turda her fixture icin su dosyalar doldurulmadan
`expected.varshaphala_tajika_rectification` alanina final deger yazilmaz:

- `references/chart_a_varshaphala_tajika.txt`
- `references/chart_b_varshaphala_tajika.txt`
- `references/chart_c_varshaphala_tajika.txt`

### Aktarilacak Alanlar

- Solar Return / Varsha yil baslangic ve bitisi
- Varsha Lagna
- Muntha burcu, evi ve lordu
- Varshesha aday rolleri ve final hakemlik notu
- Mudda Dasha baslangic lordu ve olay tarihindeki aktif lord
- Punya, Karma ve Vivaha Saham formulleri ve varsa gun/gece varyant karari
- Tajika aspekt/orb/Deeptamsa kurali
- Ithasala/Isarapha ve diger Tajika yoga adaylari icin final kabul kosullari
- Hangi katmanin rektifikasyon skorunda kullanilabilecegi veya kullanilamayacagi

Kontrol notu:
- Ham dis kaynak ciktisi once referans dosyasina eklenir.
- Kaynak parampara veya yazilim ayarlari belirtilmeden expected alan
  doldurulmaz.
- Starter Saham/Tajika katmanlari golden uyum olmadan rektifikasyon agirligi
  yapilmaz.

## Uyum Karari

Swiss Ephemeris ve JHora farklari icin ilk karar sirasi:

1. Timezone ve UTC donusumu kontrol edilir.
2. Ayanamsa ve node ayari kontrol edilir.
3. Koordinat hassasiyeti kontrol edilir.
4. Hala fark varsa fixture `notes` veya referans dosyasina fark notu yazilir.
5. Tolerans disi farklarda otomatik test yazilmaz; once kaynak karari istenir.

## Kapsam Disi

- Yeni kutuphane veya arac kurmak
- Mevcut API/generator davranisini degistirmek
- Obsidian dosyalarindan referans uretmek
- Yorum metinlerini golden test kabul etmek
