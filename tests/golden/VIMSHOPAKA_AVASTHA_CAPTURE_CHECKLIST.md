# Vimshopaka ve Avastha Capture Checklist

Bu dosya, `fixtures.json` icindeki `chart_a`, `chart_b` ve `chart_c` icin
Vimshopaka Bala ve Avastha degerleri golden expected alanlarina yazilmadan once
hangi ham referans bilgilerinin toplanacagini tarif eder.

Bu adim kod, generator, UI veya Obsidian kisi dosyasi degistirmez.

## Genel Kaynak Ayarlari

Her referans kaydinda su ayarlar acikca yazilmalidir:

- Ayanamsa: Lahiri
- Zodiac: sidereal
- Nodes: true node / true Rahu
- Birth time: fixture icindeki yerel saat
- Timezone/UTC offset: fixture icindeki deger
- Latitude/longitude: fixture icindeki koordinatlar
- Dasha/varga/avastha ekrani hangi yazilimdan alindi
- Yazilim versiyonu veya kaynak adi
- Kullanilan Vimshopaka scheme ve agirlik seti
- Kullanilan Avastha kural ailesi

## Fixture Dosyalari

Ham referanslar once mevcut JHora referans dosyalarina eklenir:

| Fixture | Referans dosyasi |
| --- | --- |
| `chart_a` | `references/chart_a_jhora.txt` |
| `chart_b` | `references/chart_b_jhora.txt` |
| `chart_c` | `references/chart_c_jhora.txt` |

Expected alanlari ham referans dosyalari doldurulmadan yazilmaz.

## Analiz 1: Vimshopaka Bala

### Kullanilacak Veri Listesi

- D1, D2, D3, D7, D9, D12, D30 varga yerlesimleri
- Gezegen burcu ve burc yoneticisi
- Gezegen dignity/relationship durumu
- Kullanilan scheme:
  - Shadvarga
  - Saptavarga
  - varsa Dashavarga
  - varsa Shodashavarga
- Her scheme icin division agirliklari
- Her gezegen icin raw skor
- Her gezegen icin normalized skor veya grade

### Toplanacak Ham Alanlar

Her fixture ve her gorunur gezegen icin:

```text
## Vimshopaka Bala

Source:
Version:
Scheme:
Weights:
Notes:

| Planet | Scheme | Division | Sign | Sign Lord | Dignity/Relation | Weight | Raw Points | Notes |
| --- | --- | --- | --- | --- | --- | ---: | ---: | --- |
| Sun | Saptavarga | D1 |  |  |  |  |  |  |

## Vimshopaka Summary

| Planet | Shadvarga Raw | Shadvarga Grade | Saptavarga Raw | Saptavarga Grade | Notes |
| --- | ---: | --- | ---: | --- | --- |
| Sun |  |  |  |  |  |
```

### Kapsam Disi

- Rahu/Ketu icin ilk geciste skor yazmak
- Farkli scheme'leri tek dogruymus gibi birlestirmek
- `fixtures.json` expected alanlarini hemen doldurmak
- API `score_status` degerini final yapmak

### Risk / Belirsizlik

- Vimshopaka scheme ve agirlik setleri kaynaklara gore degisebilir.
- Yazilim raw skor ve normalized skor birimlerini farkli gosterebilir.
- Varga hesap farki varsa Vimshopaka sonucu da farkli cikar.

## Analiz 2: Avasthalar

### Kullanilacak Veri Listesi

- Gezegen burc ici derecesi
- Odd/even sign bilgisi
- Dignity veya relationship bilgisi
- Combustion ve retrograde bilgisi
- Ev ve conjunction bilgisi
- Kaynagin kullandigi Avastha kural ailesi

### Toplanacak Ham Alanlar

Her fixture ve her gorunur gezegen icin:

```text
## Avasthas

Source:
Version:
Rule family:
Notes:

| Planet | Degree in Sign | Bala Avastha | Jagradadi Avastha | Deeptadi Avastha | Lajjitaadi Avastha | Score/Points | Notes |
| --- | ---: | --- | --- | --- | --- | ---: | --- |
| Sun |  |  |  |  |  |  |  |
```

Ek kural notlari:

```text
## Avastha Rule Notes

- Bala odd sign order:
- Bala even sign order:
- Jagradadi rule basis:
- Deeptadi rule basis:
- Lajjitaadi rule basis:
- Combustion handling:
- Retrograde handling:
- Conjunction orb:
- House-system dependency:
```

### Kapsam Disi

- Avastha degerlerinden yorum metni uretmek
- Avastha skorunu rektifikasyon skoruna baglamak
- Rahu/Ketu icin kaynaksiz veya tartismali skor yazmak
- Deeptadi/Lajjitaadi degerlerini kaynak kurali belirsizken kesin kabul etmek

### Risk / Belirsizlik

- Avastha tek bir hesap ailesi degildir; ayni ad farkli kaynaklarda farkli
  kuralla kullanilabilir.
- Bala Avastha odd/even sign siralamasi ters uygulanirsa tum tablo bozulur.
- Lajjitaadi ev, conjunction ve combustion yorumuna bagli oldugu icin dogum
  saati ve ev sistemi hassasiyeti yuksektir.

## Fark Notu Standardi

Kaynaklar veya API ciktisi arasinda fark varsa ilgili `chart_*_jhora.txt`
dosyasina su blok eklenir:

```text
## Vimshopaka / Avastha Difference Notes

- Field:
- API value:
- Reference value:
- Difference:
- Likely cause:
- Decision:
```

## Fixture Guncelleme Kurali

1. Once ham referans ilgili `references/chart_*_jhora.txt` dosyasina eklenir.
2. Her fixture icin kaynak ayarlari ve kural ailesi yazilir.
3. Uc fixture ayni kural setiyle tutarli gorulurse expected doldurma adimi
   ayrica planlanir.
4. Fark varsa `expected.source_status` final hale getirilmez.
5. `expected.vimshopaka_bala` ve `expected.avasthas` alanlari kullanici
   onayi olmadan `null` durumundan cikarilmaz.
