# Golden Test Paketi Plani

Bu klasor, Vedik hesap motoru icin dis referanslarla dogrulanacak golden test
verilerini tutmak icin ayrilmistir.

Bu asamada dosyalar test calistirmaz. Amac, hangi chartlarin hangi kaynaklarla
ve hangi toleranslarla dogrulanacagini netlestirmektir.

## Kapsam

- D1 gezegen boylamlari
- Lagna ve ev teknik kontrolu
- Ay nakshatra ve pada
- Vimshottari aktif dasha zinciri
- Ilk varga kontrolleri: D9, D10, D7
- Ileride eklenecek katmanlar icin hazir alanlar: Bhava Chalit, Vimshopaka,
  Avastha, Tajika, diger dasha sistemleri, transit ingress

## Kaynak Onceligi

| Katman | Birincil referans | Ikincil kontrol |
| --- | --- | --- |
| Gezegen boylamlari | Swiss Ephemeris / swetest | Mevcut API ciktisi |
| Lagna ve evler | Swiss Ephemeris / swetest | Mevcut API ciktisi |
| Vedic chart karsilastirma | Jagannatha Hora | Manuel ikinci yazilim ciktisi |
| Panchanga / nakshatra | Swiss Ephemeris + formul testi | Jagannatha Hora |
| Dasha motorlari | Klasik formul + Jagannatha Hora | Mevcut Vimshottari testi |
| Tajika / Varshaphala | Klasik formul + Jagannatha Hora | Mevcut Varshaphala core |
| Transit / ingress | Swiss Ephemeris / swetest | Mevcut transit pack |

## Tolerans Matrisi

| Veri alani | Ilk tolerans | Not |
| --- | ---: | --- |
| Gezegen boylami | +/- 0.05 derece | Ilk golden test icin yeterli. |
| Ay boylami | +/- 0.03 derece | Nakshatra sinirlarinda boundary_case isaretlenir. |
| Lagna derecesi | +/- 0.10 derece | Saat ve timezone farkina duyarlidir. |
| Ev cusp / Sripati cusp | +/- 0.15 derece | Ev sistemi ve koordinat farki etkiler. |
| Nakshatra | birebir | Sinir durumlari fixture icinde isaretlenir. |
| Pada | birebir | Ilk sette sinir chart secilmez. |
| Dasha baslangic/bitis | +/- 1 gun | Yil uzunlugu kabul farklari olabilir. |
| Antardasha / pratyantar | +/- 1 gun | Sookshma icin ileride daha dar tolerans acilabilir. |
| Varga burcu | birebir | Sinir derecelerde boundary_case gerekir. |
| Transit ingress zamani | +/- 2 saat | Ilk asama toleransidir. |
| Panchanga anga | birebir | Sinir anlarinda boundary_case gerekir. |

## Ilk Chart Seti

| Chart | Amac | Secim kriteri |
| --- | --- | --- |
| chart_a | Temel D1 / gezegen / lagna dogrulama | Gezegenler nakshatra ve burc sinirindan uzak. |
| chart_b | Turkiye timezone / DST guvenligi | Turkiye dogum yeri ve tarih bazli timezone kontrolu. |
| chart_c | Dasha + varga dogrulama | Ay nakshatra derecesi temiz, D9/D10/D7 kontrolu uygun. |

## Kapsam Disi

- Yorum dogrulama testi
- Musteri veya mevcut Obsidian dosyalari uzerinden test
- UI dogrulamasi
- Generator davranisini degistirmek
- Eksik klasik katmanlari tamamlanmis gibi gostermek

## Rektifikasyon Guvenlik Siniri

Golden fixture'lar hesap zeminini korumak icindir; rektifikasyon aday
pencerelerini daraltmak veya tek saat sonucunu zorlamak icin kullanilmaz.

Golden kontroller su teknik alanlarda yardim eder:

- timezone
- ayanamsa
- gezegen boylami
- Rahu/Ketu ekseni
- nakshatra/pada
- dasha ve varga teknik dogrulugu

Golden kontroller sunlari yapmaz:

- aday saat penceresini kapatmaz
- tek rektifiye saat ilan etmez
- heuristic skoru istatistiksel olasilik gibi sunmaz
- yorum/tahmin esnekligini kaldirmaz
- kullaniciya gorunen analiz dilini otomatik degistirmez

Rektifikasyon tarafinda dogruluk artarken yorum ve aday pencere esnekligi
korunmalidir.

## Uygulama Notu

Otomatik test dosyasi ancak fixture degerleri dis kaynaklarla doldurulup
kullanici onayi alindiktan sonra eklenmelidir.

## Pasif Yardimci Komutlar

Bu komutlar API, generator, UI veya Obsidian dosyalarini degistirmez.

Swiss referans ciktisini ekrana yazdirma:

```bash
cd progresif-vedik-chart
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python tests/golden/generate_swiss_references.py --fixture chart_a
```

Swiss referans dosyalarini bilerek yeniden yazma:

```bash
cd progresif-vedik-chart
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python tests/golden/generate_swiss_references.py --write
```

Fixture ve referans sablon sekil kontrolu:

```bash
cd progresif-vedik-chart
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python tests/golden/validate_fixture_shape.py
```

Beklenen mevcut durum:

- `source_status` simdilik `swiss_only_pending_jhora`.
- JHora, Vimshottari, D9, D10 ve D7 alanlari pending uyarisi verebilir.
- Swiss ve JHora referans dosyalarinda Bhava Chalit / Sripati basliklari
  bulunmalidir.
- Varshaphala/Tajika rektifikasyon referans sablonlari
  `references/chart_*_varshaphala_tajika.txt` icinde bulunmalidir.
- Bu uyarilar JHora bagimsiz kontrolu tamamlanana kadar hata sayilmaz.
- Vimshopaka Bala ve Avastha ham referanslari icin dar yakalama standardi:
  `VIMSHOPAKA_AVASTHA_CAPTURE_CHECKLIST.md`.
