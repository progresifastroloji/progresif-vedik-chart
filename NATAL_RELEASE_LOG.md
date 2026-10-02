# Natal veri paketi — 2 Ekim 2026

Kullanıcı yetkisi: dört karakter göstergesi ve nakşatra anlamlarını önceliklendir; belirtilen profil biliniyor/rektifikasyonlu olsun; uygula, yayınla ve soruyla test et.

Yapılacaklar: eski hesap katmanlarını mevcut motorla yenile; güncel daşa; dört öncelikli çapa ve ayrık zincirler; nakşatra/pada anlamları; doğru Shadbala; boş tablo/tekrar azaltımı; sabit 33 bölüm kimliği ve indeks bütünlüğü; kontrollü yayın ve canlı soru.
Yapılmayacaklar: yeni model, yeni okul, geniş müşteri değişikliği, ilgisiz çalışma değişikliklerinin yayını.
Değişmeden kalacaklar: mevcut rehberlik kişiliği, API uçları, dış doğrulama durumları, yaklaşık/bilinmeyen saat politikası, mevcut uygulama sözleşmesi.

Kaynak: canlı Railway accurate-victory / production / vedic-api, progresifastroloji/progresif-vedik-chart claude/vedic-chart-app-a4HZU @3b6dddb. Temiz ayrı çalışma kopyası codex/natal-character-evidence. Ana kopyalardaki önceki değişiklikler korunuyor.

Durum: uygulama, iki kontrollü yayın, güncel dosya bütünlüğü ve gerçek canlı soru doğrulandı. Son anlatıdaki ev konumu/lordluk ifade hatası ile sınırlı disk alanı ayrı kalan bulgulardır.
Kök nedenler: tarihsel snapshot güncellenmeden dosyalanıyor; eksik profesyonel güç statüsü zayıf diye varsayılıyor; ilk alt başlık siliniyor; aynı kanıt çok kez tekrarlanıyor.

## Yerel doğrulama
- Natal paket/metodoloji/dosya: 90 test geçti. Son ilişki projeksiyonu için paket tekrar kontrolü sürüyor.
- Geniş API/sohbet paketi: 143 test ilk çalışmada 7 başarısızlık + 4 hata verdi. Üç hata eksik sentetik harita yükseltme sınırında düzeltildi; iki beklenti açık rektifikasyon davranışına güncellendi.
- Kalan 6 test (D16 eski fixture, Graha Yuddha iki eski beklenti, transit metin iki eski beklenti, Vault Panchanga eski referans) temiz 3b6dddb kopyasında aynı şekilde başarısız: 5 failure + 1 error. Kapsam dışı; geçiyormuş gibi raporlanmayacak.
- Açık rektifikasyon ve natal karakter tekrar kontrolü: 8/8 geçti; Vault etiketi doğrulaması geçti.
- Web: 102 PWA testi, TypeScript ve OpenNext üretim derlemesi geçti. İlk ortak dependency ağacında font hatası; ayrı kilitli npm ci kurulumuyla düzeldi. Yeni paket/sürüm eklenmedi.
- Supabase additive migration uygulandı; yalnız rectified değeri doğrulamalara eklendi. Eski kayıtlar değişmedi; RPC erişimleri ve kilitli wrapper korundu; advisor çıktısı öncesi/sonrası aynı.

## Yayın ve canlı kabul
- API `bb2d08a`, Railway `f2a38d7f-f04b-4289-bfb8-a06955f40621`: doğru servis üzerinde aktif/başarılı görüldü. Web `bc9bbcc` ve `58b4558`, Cloudflare `4fe5b9e4-dbe4-45b5-a95e-700cc2426e6e` yayımlandı.
- Canlı `levo` kendi profilinde Biliniyor, rektifikasyonlu seçimi yeniden açılan düzenleme ekranında korunuyor. Haritam D1/D9 yüksek güven gösteriyor; yaklaşık/bilinmeyen saatler değiştirilmedi.
- Normal Vedic AI ekranında dört nakşatranın karakter örüntüsü soruldu. İş `4f2edf64-271c-4dbf-842a-e0c0e52a10aa`, answered/completed; 30.266 ms. Teknik ve anlatı birer çağrı, toplam 57.584 token. Sade ve Pro alanları tamamıyla yerel kabul belgesine alındı; eğitim verisi yapılmadı.
- Kanıtlar dört doğru nakşatra/pada, Güneş 1.4392 ve Satürn 1.2682 Shadbala oranları, D9 desteği/karşı göstergeler içeriyor. Transit aralığı 2026-10-02–2027-01-01 yenilendi. Mevcut raw çıktı modu ve rehberlik 1.8.0 değiştirilmedi.
- Web yöneticisinin birden çok hak satırı görebilmesi nedeniyle `.maybeSingle()` başarısızdı; kendi kullanıcı kimliği filtresi eklendi. 103/103 Web testi, TypeScript ve üretim derlemesi geçti; canlı SORU HAKKI SINIRSIZ ve soru kabulü görüldü. Hak bakiyeleri/erişimler değiştirilmedi.

## Disk doluluğu ve geri alınabilir kurtarma
- İsim geri yükleme sırasında kaynak disk yazımı Errno 28 ile başarısız oldu; kısmi harita oluştu. /data toplam 433 MB, boş 0 idi. Aynı kullanıcıya ait üç eski/superseded üretilmiş klasör ve sekiz yarım yazım dosyası yedeklendi; 88 arşiv üyesinin SHA değerleri doğrulandı.
- Arşiv kullanıcının bilgisayarına indirildi: Downloads/natal-recovery-20261002.tar.gz, SHA256 344ac01549927e22aa62e73ee8353088ec46fe54923190c902928b5644fc2ab3. Doğrulanmış eski üretilmiş kopyalar /app altına taşındı; aktif dosya, veritabanı veya başka müşteri verisi silinmedi.
- 78 MB açıldı. Normal 15 dakikalık istek penceresi dolunca aynı yarım kalan iş normal current-chart yoluyla tamamlandı; status ready / reservation completed. Limit/koruma/bakiye değişmedi. Soru sonrası boş alan 66 MB: kalıcı kapasite riski sürüyor.

## Son dosya incelemesi
- Canlı dosya 98.878 bayt, 33 bölüm; Vedik Omurga 5. sırada Lagna/D1'den önce. İlk kontrolün başlık araması İngilizce Vedic kullandığı için yanlış false verdi; Türkçe Vedik başlığı dosyadan doğrulandı. Gerçek başlık-only boş tablo 0.
- Ancak yaşam olayları bölümünde yalnız yokluk satırı taşıyan tablo kaldığı görüldü; kaynak yokken tablo yerine açıklama, kaynakta olay varken gerçek satırlar korunacak şekilde düzeltildi.
- Omurga özet tablosu artık ayrık nakşatra zincirinin benzersiz adımlarını ve döngü hedefini gösteriyor. Eski JSON lord_chain tüketicileri değişmedi. Evidence revision v2 eski dosyanın yeniden üretilmesini sağlar.
- Son paket regresyonları 8/8 geçti; kayıtsız/boş/gerçek olay ayrımı, dört öncelik, zincir tekrarının olmaması, byte/hash/33 bölüm kontrolleri dahil. Artifact tekrar kullanımı ve gerçek bağlam boyutu 2/2 geçti.

## Nihai doğrulama
- Son kod `1b28b0a`, Railway `2eab7ea2-6bec-4c32-b355-ed5684906687` ACTIVE. Web Cloudflare `4fe5b9e4` %100 trafikte ayrıca panelden doğrulandı.
- Aynı doğum bilgileriyle kendi profilinin normal yeniden hazırlama yolu kullanıldı; compact_natal_v1 v2 dosyası hem Railway hem Supabase üzerinden ready oldu. Kaynak dosya 98.729 bayt, 33 bölüm / 107 tablo, boş veya yalnız yokluk satırı taşıyan tablo 0. Manifestte tüm bölüm baytları ve hashler doğrulandı; dört öncelik ve ayrı zincirler korunuyor.
- Son kaynak SHA256 `802fb0393a642600a0f18f05f64e10505c58f3c224e68f8304a5a1ad7a86e61d`. Kullanıcı bilgisayarındaki 07_natal-interpretation_CANLI_20261002.txt son dosyadır.
- Son gerçek soru işi `88ad3759-badc-43d1-8c57-9814fe32a07d` answered/completed; 38.412 ms; teknik/anlatı birer çağrı; 58.238 token. Dört nakşatra Pro metninde ve somut öneriler Sade metninde kullanıldı. İki görünüm tam olarak 08_natal-son-canli-yorumlar-20261002.md, ekran 09_natal-son-canli-kabul-20261002.jpg dosyasında korunuyor; kişisel belgeler Git'e alınmadı.
- Son Pro metinde “8. ve 6. ev lordlukları” ifadesi hatalıdır: bunlar Satürn/Venüsün konumları; doğru lordluklar 1./2. ve 5./10. Kaynak Aktif Gezegen Teknik Özeti doğru. Metin değiştirilmeden bulgu işaretlendi; bu görevde yeni anlatı filtresi/model/çıktı modu seçilmedi ve kusursuz anlatı iddia edilmiyor.
- Son boş alan 42 MB. Kalıcı kapasite genişletme veya ödeme uygulanmadı. Önceden mevcut altı geniş API test uyumsuzluğu da giderilmiş sayılmıyor.
- Son operasyon kaydı ayrı codex/natal-character-evidence dalına gönderilir; çalışan kodun üretim kaynağı 1b28b0a olarak kalır. Web proje kayıtları aynı doğrulanmış durumu içerir.
