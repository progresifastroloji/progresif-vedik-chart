# Gemini'ye Giden Vedik Kaynaklar

Bu klasör, Gemini istemlerini incelemek veya başka bir ortama aktarmak için Markdown dışa aktarımlarını tutar.

## Sabit kaynaklar

1. [`01_SYSTEM_METHODOLOGY.md`](./01_SYSTEM_METHODOLOGY.md) — Teknik Vedik/Jyotiṣa analizinin tek aktif metodolojisi.
2. [`02_VEDIC_GUIDANCE_METHODOLOGY.md`](./02_VEDIC_GUIDANCE_METHODOLOGY.md) — Doğrulanmış teknik sonucu sade kişisel anlam ve güvenli rehberliğe çeviren, yalnız anlatı aşamasında kullanılan metodoloji.

Bu iki Markdown dosyası, çalışma zamanında kullanılan aşağıdaki bütünlük kontrollü kaynakların Gemini incelemesi için dışa aktarımıdır. Değişikliklerde `.txt` kaynakları ve manifest önceliklidir:

- `../SYSTEM_METHODOLOGY.txt`
- `../VEDIC_GUIDANCE_METHODOLOGY.txt`

## Kullanıcıya göre çalışma zamanı kaynakları

Gemini’ye gönderilen natal ve transit kaynakları sabit dosya değildir. Kullanıcının doğrulanmış haritasından, sahiplik ve SHA-256 kontrolü yapıldıktan sonra çalışma zamanında okunur:

- `natal-interpretation.md` — Her normal sohbet sorusunda kullanıcıya ait natal kaynak.
- `transit-three-month.md` — Zamanlama/transit bağlamı gerektiğinde kullanılan, kullanıcıya ait üç aylık transit kaynağı.

Bu iki dosyanın genel kopyası repoya alınmaz; kişisel doğum ve harita verisi içerebilir. Gemini’ye gönderilmeden önce sunucu tarafında kanıt paketiyle eşleştirilir. Bu klasördeki Markdown dosyaları genel metodoloji kaynaklarıdır; kişisel kullanıcı verisi içermez.

## Gönderim sırası

Anlatı çağrısında doğrulanmış Aşama 1 JSON’u ile birlikte teknik metodoloji ve rehberlik metodolojisi kullanılır. Tam kaynak modu açıksa kaynak sırası `SYSTEM_METHODOLOGY → natal-interpretation → transit-three-month` olarak korunur. Teknik Aşama 1 çağrısı rehberlik metodolojisini almaz.

Bu dışa aktarımlar runtime’ın yeni bir kaynak seçmesine izin vermez; değişiklik yapılacaksa önce `.txt` kaynakları ve SHA-256 manifesti güncellenmeli, ardından Markdown dışa aktarımları senkronize edilmelidir.
