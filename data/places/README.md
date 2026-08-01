# Doğum Yeri Kataloğu

Bu klasördeki `places.sqlite3`, GeoNames `cities500` verisinden üretilir.
Kaynak veri CC BY 4.0 lisanslıdır: https://download.geonames.org/export/dump/

Katalog yaklaşık 185.000 şehir, kasaba ve idari merkezi kapsar. Her kayıtta
koordinatlar ile IANA saat dilimi kimliği birlikte tutulur. Böylece API doğum
tarihindeki tarihsel UTC farkını ve yaz saati uygulamasını hesaplayabilir.

Oluşturma:

```bash
.venv/bin/python scripts/build_places_catalog.py
```

Üretilen SQLite dosyası Git'e eklenmez. Railway imajı hazırlanırken aynı komut
çalıştırılacak ve `VEDIC_PLACES_DB` değişkeni dosyanın konumunu gösterecektir.
