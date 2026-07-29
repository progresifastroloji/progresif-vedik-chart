# Golden Expected Fields

Bu dosya, `references/` altindaki ham dis kaynak ciktisindan
`fixtures.json` icindeki `expected` alanlarina hangi verilerin aktarilacagini
standartlastirir.

Bu asamada otomatik test yoktur. Once dis referanslar doldurulur, sonra bu
listeye gore beklenen degerler elle veya kontrollu bir yardimciyla aktarilir.

## D1 / Lagna

`expected.lagna` icin hedef alanlar:

```json
{
  "sign": "Aries",
  "sign_index": 0,
  "degree": 12.3456,
  "degree_str": "12°20'44\""
}
```

Kontrol notu:
- `sign_index` Aries = 0 kabulune gore yazilir.
- Derece sadece burc ici derece olmalidir, toplam zodiac boylami degil.
- Whole Sign ana ev sistemi korunur; cusp veya Sripati degerleri ileride ayri
  alan olarak eklenir.

## D1 / Gezegenler

`expected.planets` icin hedef alanlar:

```json
{
  "Sun": {
    "longitude": 270.1234,
    "sign": "Capricorn",
    "sign_index": 9,
    "degree": 0.1234,
    "degree_str": "00°07'24\"",
    "retrograde": false
  }
}
```

Ilk sette kontrol edilecek gezegenler:

- Sun
- Moon
- Mars
- Mercury
- Jupiter
- Venus
- Saturn
- Rahu (True)
- Ketu

Kontrol notu:
- `longitude` sidereal toplam zodiac boylami olmalidir.
- Rahu icin true node kullanilir.
- Ketu, Rahu'ya karsi 180 derece olarak dogrulanir.

## Ay Nakshatra

`expected.moon_nakshatra` icin hedef alanlar:

```json
{
  "name": "Ashwini",
  "number": 1,
  "pada": 1,
  "lord": "Ketu",
  "degree_in_nakshatra": 1.2345
}
```

Kontrol notu:
- Nakshatra ve pada birebir eslesmelidir.
- Sinira yakin chart varsa `flags.boundary_case` true yapilir.

## Vimshottari Aktif Dasha

`expected.vimshottari_active` icin hedef alanlar:

```json
{
  "reference": "birth",
  "path": ["Sun", "Moon", "Mars"],
  "maha": {
    "lord": "Sun",
    "start": "1999-01-01",
    "end": "2005-01-01"
  },
  "antara": {
    "lord": "Moon",
    "start": "2000-01-01",
    "end": "2000-06-01"
  },
  "pratyantar": {
    "lord": "Mars",
    "start": "2000-02-01",
    "end": "2000-02-20"
  }
}
```

Kontrol notu:
- Ilk golden sette dogum ani aktif zincir yeterlidir.
- Tarih farki toleransi `default_tolerances.dasha_date_days` ile kontrol edilir.
- Sookshma daha sonra eklenebilir.

## Chara Antardasha / Yogini Pratyantardasha

`expected.chara_antardasha` icin ilk hedef alanlar:

```json
{
  "status": "implemented_starter_chara_maha_antara",
  "levels": ["maha", "antara"],
  "active_path": ["Aries", "Leo"],
  "current_active_path": ["Cancer", "Scorpio"],
  "score_status": "technical_only"
}
```

`expected.yogini_pratyantardasha` icin ilk hedef alanlar:

```json
{
  "status": "implemented_starter_yogini_maha_antara_pratyantar",
  "levels": ["maha", "antara", "pratyantar"],
  "active_path": ["Mangala", "Dhanya", "Siddha"],
  "current_active_path": ["Ulka", "Siddha", "Sankata"],
  "score_status": "technical_only"
}
```

Kontrol notu:
- Bu alanlar zamanlama capraz kontrolu icindir; tek basina olay tahmini veya
  rektifikasyon karari uretmez.
- Chara Antardasha ilk uygulamada dusuk guvenli starter teknik tablodur;
  parampara-specific varyantlar golden referans olmadan final kabul edilmez.
- Yogini Pratyantardasha, Maha ve Antara zincirinin ayni oransal Yogini sirasiyla
  bir alt seviyeye indirilmis halidir.
- Golden expected degerleri ancak dis referans tarihi ve aktif path birebir
  dogrulandiktan sonra doldurulur.

## Vargas

`expected.vargas` icin ilk hedef alanlar:

```json
{
  "D9": {
    "lagna": {
      "sign": "Aries",
      "sign_index": 0
    },
    "planets": {
      "Sun": {
        "sign": "Aries",
        "sign_index": 0
      }
    }
  }
}
```

Ilk sette kontrol edilecek vargalar:

- D9
- D10
- D7

Kontrol notu:
- Ilk asamada varga burcu birebir kontrol edilir.
- Varga derece kontrolu daha sonra eklenebilir.

## Bhava Chalit / Sripati

`expected.bhava_chalit` ileride eklendiginde hedef alanlar:

```json
{
  "source_status": "swiss_only_pending_jhora",
  "method": "sripati_bhava_chalit",
  "houses": [
    {
      "house": 1,
      "cusp_longitude": 26.630963,
      "cusp_sign": "Aries",
      "cusp_sign_index": 0,
      "cusp_degree": 26.630963,
      "start_longitude": 11.630963,
      "end_longitude": 41.630963,
      "lord": "Mars"
    }
  ],
  "planets": {
    "Moon": {
      "longitude": 12.718052,
      "whole_sign_house": 1,
      "bhava_chalit_house": 1,
      "house_changed": false,
      "distance_from_cusp": 13.912911
    }
  },
  "summary": {
    "changed_house_count": 0,
    "changed_planets": [],
    "birth_time_sensitive": true
  }
}
```

Kontrol notu:
- Bu alan Whole Sign ev sistemini degistirmez; sadece ikinci teknik bhava
  referansi olarak tutulur.
- `houses[].start_longitude` ve `houses[].end_longitude` 360 dereceyi asabilir;
  karsilastirma yaparken normalize edilmelidir.
- `planets[].whole_sign_house` mevcut D1 ev bilgisidir.
- `planets[].bhava_chalit_house` Sripati bhava araligina gore teknik evdir.
- `house_changed` yalniz teknik fark bayragidir; yorum veya kesin hukum
  uretmez.
- Rektifikasyon ve tahmin pencereleri bu alanla kapatilmaz.
- Dogum saati guveni dusukse `birth_time_sensitive` uyarisi korunur.
- Bu alan generator veya kullaniciya gorunen yorum diline ayri onay olmadan
  eklenmemelidir.

## Bhava Bala / Ev Bazli Kanit Tablosu

`expected.bhava_bala` ileride eklendiginde hedef alanlar:

```json
{
  "source_status": "swiss_only_pending_jhora",
  "status": "starter_technical_layer",
  "method": "compiled_house_evidence_from_existing_layers_no_new_weighting",
  "houses": [
    {
      "house": 1,
      "sign": "Aries",
      "sign_index": 0,
      "lord": "Mars",
      "occupants": ["Moon"],
      "graha_aspected_by": ["Saturn"],
      "rashi_aspected_by": ["Jupiter"],
      "ashtakavarga": {
        "sav": 28,
        "lord_bav": 4
      },
      "lord_shadbala": {
        "total_score": 123.45,
        "grade": "moderate"
      },
      "bhava_chalit": {
        "cusp_sign": "Aries",
        "changed_planets_touching_house": []
      },
      "score": null,
      "score_status": "not_scored"
    }
  ],
  "summary": {
    "house_count": 12,
    "scored": false,
    "birth_time_sensitive": true
  }
}
```

Kontrol notu:
- Bu alan yeni klasik Bhava Bala formulu veya agirlikli ev puani degildir.
- Ilk asamada `houses`, `lordships`, `aspects`, `ashtakavarga`,
  `shadbala` ve `bhava_chalit` alanlarindan derlenen kanit tablosudur.
- `score` bilincli olarak `null`, `score_status` `not_scored` kalir.
- `summary.scored` false oldugu surece bu alan yorum gucu, kesin hukum veya
  siralama olarak kullanilmaz.
- Rektifikasyon ve tahmin pencereleri bu alanla kapatilmaz.
- Golden expected degeri ancak kaynak alanlarin her biri dis referansla uyumlu
  hale geldikten sonra doldurulabilir.

## Vimshopaka Bala

`expected.vimshopaka_bala` ileride eklendiginde hedef alanlar:

```json
{
  "status": "starter_technical_layer",
  "score_status": "not_final",
  "schemes": {
    "shadvarga": {
      "status": "available_pending_reference_validation",
      "divisions": ["D1", "D2", "D3", "D9", "D12", "D30"],
      "weights_status": "pending_reference_validation"
    },
    "saptavarga": {
      "status": "available_pending_reference_validation",
      "divisions": ["D1", "D2", "D3", "D7", "D9", "D12", "D30"],
      "weights_status": "pending_reference_validation"
    }
  },
  "planets": {
    "Sun": {
      "schemes": {
        "saptavarga": {
          "raw_score": null,
          "normalized_score": null,
          "score_status": "not_final",
          "rows": [
            {
              "division": "D1",
              "sign": "Aries",
              "sign_lord": "Mars",
              "dignity": "friend",
              "confidence": "high"
            }
          ]
        }
      }
    }
  },
  "summary": {
    "visible_planets_only": true,
    "rahu_ketu_scored": false,
    "scored": false,
    "rectification_score_used": false
  }
}
```

Kontrol notu:
- Ilk asamada bu alan pasif teknik tablodur.
- `score_status` final olmayacak; agirliklar dis kaynak/golden referansla
  dogrulanmadan rektifikasyon skoruna baglanmaz.
- Rahu/Ketu ilk uygulamada skorlanmaz; sadece `excluded` veya `not_scored`
  olarak isaretlenebilir.
- Eksik veya tartismali scheme/division setleri `not_available` ya da
  `partial` olarak acik kalir.
- Ayrintili plan: `docs/VIMSHOPAKA_BALA_PLAN.md`.

## Avasthalar

`expected.avasthas` ileride eklendiginde hedef alanlar:

```json
{
  "status": "starter_technical_layer",
  "score_status": "not_scored",
  "rules_status": {
    "bala_avastha": "pending_reference_validation",
    "jagradadi_avastha": "pending_reference_validation",
    "deeptadi_avastha": "pending_reference_validation",
    "lajjitaadi_avastha": "not_available_pending_rules"
  },
  "planets": {
    "Sun": {
      "degree_in_sign": 10.5,
      "sign": "Aries",
      "house": 1,
      "bala_avastha": {
        "status": "available_pending_reference_validation",
        "value": null,
        "score": null,
        "score_status": "not_scored"
      },
      "jagradadi_avastha": {
        "status": "pending_reference_validation",
        "value": null,
        "score": null,
        "score_status": "not_scored"
      },
      "deeptadi_avastha": {
        "status": "pending_reference_validation",
        "value": null,
        "score": null,
        "score_status": "not_scored"
      },
      "lajjitaadi_avastha": {
        "status": "not_available_pending_rules",
        "value": null,
        "score": null,
        "score_status": "not_scored"
      }
    }
  },
  "summary": {
    "visible_planets_only": true,
    "rahu_ketu_scored": false,
    "scored": false,
    "birth_time_sensitive": true,
    "rectification_score_used": false
  }
}
```

Kontrol notu:
- Ilk asamada bu alan pasif teknik kanit tablosudur.
- Bala, Jagradadi, Deeptadi ve Lajjitaadi ayni sistem gibi
  birlestirilmemelidir; her biri ayri status ve rule basis ile tutulur.
- `score_status` `not_scored` kalir; golden referans olmadan rektifikasyon
  skoruna veya final yorum gucune baglanmaz.
- Rahu/Ketu ilk uygulamada skorlanmaz.
- Ayrintili plan: `docs/AVASTHA_PLAN.md`.

## expected.varshaphala_tajika_rectification

Ilk pasif alan:

```json
{
  "varshaphala_tajika_rectification": null
}
```

Kontrol notu:
- Bu alan Varshaphala/Tajika katmanlarini rektifikasyon skoruna baglamak icin
  degil, baglamadan once gereken golden dogrulama zeminini izlemek icindir.
- Muntha, teknik Varshesha adayi ve aktif Mudda lordu mevcut cekirdek
  rektifikasyon kaniti olarak ayri tutulur.
- Saham starter, Tajika aspekt starter, Ithasala/Isarapha, Tajika yoga aday
  envanteri ve Deeptamsa/orb diagnostik alanlari `not_scored` kalir.
- Bu alan doldurulmadan yeni Varshaphala/Tajika rektifikasyon agirligi
  eklenmemelidir.
- Ayrintili plan: `docs/RECTIFICATION_VARSHAPHALA_TAJIKA_GOLDEN_PLAN.md`.

## Ileri Alanlar

Asagidaki alanlar simdilik fixture icinde zorunlu degildir:

- `expected.bhava_chalit`
- `expected.sripati_houses`
- `expected.bhava_bala`
- `expected.vimshopaka_bala`
- `expected.avasthas`
- `expected.chara_antardasha`
- `expected.yogini_pratyantardasha`
- `expected.narayana_dasha`
- `expected.ashtottari_dasha`
- `expected.kalachakra_dasha`
- `expected.tajika`
- `expected.sahams`
- `expected.varshaphala_tajika_rectification`
- `expected.transit_ingress`

Bu alanlar ilgili motor icin ayri onay geldikten sonra eklenmelidir.

## Veri Giris Kurali

- Ham referans ciktisi once `references/` altina eklenir.
- `fixtures.json` icindeki `expected` alanlari ancak referans kaynagi ve ayarlari
  netse doldurulur.
- Dis kaynaklar uyusmuyorsa beklenen deger yazmadan once fark notu eklenir.
- Musteri veya Obsidian kisi dosyalari golden fixture olarak kullanilmaz.
