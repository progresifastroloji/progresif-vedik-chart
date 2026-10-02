# Natal veri paketi — 2 Ekim 2026

Kullanıcı yetkisi: dört karakter göstergesi ve nakşatra anlamlarını önceliklendir; belirtilen profil biliniyor/rektifikasyonlu olsun; uygula, yayınla ve soruyla test et.

Yapılacaklar: eski hesap katmanlarını mevcut motorla yenile; güncel daşa; dört öncelikli çapa ve ayrık zincirler; nakşatra/pada anlamları; doğru Shadbala; boş tablo/tekrar azaltımı; sabit 33 bölüm kimliği ve indeks bütünlüğü; kontrollü yayın ve canlı soru.
Yapılmayacaklar: yeni model, yeni okul, geniş müşteri değişikliği, ilgisiz çalışma değişikliklerinin yayını.
Değişmeden kalacaklar: mevcut rehberlik kişiliği, API uçları, dış doğrulama durumları, yaklaşık/bilinmeyen saat politikası, mevcut uygulama sözleşmesi.

Kaynak: canlı Railway accurate-victory / production / vedic-api, progresifastroloji/progresif-vedik-chart claude/vedic-chart-app-a4HZU @3b6dddb. Temiz ayrı çalışma kopyası codex/natal-character-evidence. Ana kopyalardaki önceki değişiklikler korunuyor.

Durum: uygulama sürüyor; test/yayın/canlı kabul henüz yapılmadı.
Kök nedenler: tarihsel snapshot güncellenmeden dosyalanıyor; eksik profesyonel güç statüsü zayıf diye varsayılıyor; ilk alt başlık siliniyor; aynı kanıt çok kez tekrarlanıyor.

## Yerel doğrulama
- Natal paket/metodoloji/dosya: 90 test geçti. Son ilişki projeksiyonu için paket tekrar kontrolü sürüyor.
- Geniş API/sohbet paketi: 143 test ilk çalışmada 7 başarısızlık + 4 hata verdi. Üç hata eksik sentetik harita yükseltme sınırında düzeltildi; iki beklenti açık rektifikasyon davranışına güncellendi.
- Kalan 6 test (D16 eski fixture, Graha Yuddha iki eski beklenti, transit metin iki eski beklenti, Vault Panchanga eski referans) temiz 3b6dddb kopyasında aynı şekilde başarısız: 5 failure + 1 error. Kapsam dışı; geçiyormuş gibi raporlanmayacak.
- Açık rektifikasyon ve natal karakter tekrar kontrolü: 8/8 geçti; Vault etiketi doğrulaması geçti.
- Web: 102 PWA testi, TypeScript ve OpenNext üretim derlemesi geçti. İlk ortak dependency ağacında font hatası; ayrı kilitli npm ci kurulumuyla düzeldi. Yeni paket/sürüm eklenmedi.
- Supabase additive migration uygulandı; yalnız rectified değeri doğrulamalara eklendi. Eski kayıtlar değişmedi; RPC erişimleri ve kilitli wrapper korundu; advisor çıktısı öncesi/sonrası aynı.

Sıradaki: yalnız kapsam dosyalarının Git kaydı/gönderimi, Railway/Web yayını, kullanıcı profilini açık rectified seçimiyle kaydetmek ve gerçek soru kabulü.
