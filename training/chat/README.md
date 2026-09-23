# Vedic AI sohbet eğitim verisi

Bu klasör yalnız Vedic AI sohbet anlatımını geliştirmek için kullanılan, kimlikten arındırılmış eğitim adaylarını tutar.

## Dosyalar

- `comparison_audit_v1.jsonl`: Aynı soru için eski denetimli cevap, ham Gemini cevabı, sorun etiketleri ve önerilen doğru cevabı birlikte tutar. Bu dosya Gemini eğitimine verilmez.
- `vertex_sft_candidate_v1.jsonl`: Google Vertex AI denetimli ince ayar (SFT) biçimine uygun eğitim adaylarıdır. Yalnız astrolog onayı alan kayıtlar gerçek eğitim kümesine taşınabilir.
- `manifest_v1.json`: Her kaydın inceleme ve onay durumunu tutar.
- `validate_chat_training.py`: Dosya biçimini, kayıt eşleşmesini ve temel gizlilik sınırlarını denetler.

## Onay akışı

1. Chart API kanıtı hesaplar; model hesap yapmaz.
2. Eski cevap ve ham Gemini cevabı yalnız hata analizi için kaydedilir.
3. Önerilen doğru cevap astrolog tarafından incelenir.
4. `astrolog_review_pending` kaydı onaylanmadan eğitim işine gönderilmez.
5. Onaylanan örnekler eğitim ve doğrulama kümelerine kişi bazında değil konu/örüntü bazında ayrılır.

Bu klasörde ad, e-posta, kullanıcı kimliği, doğum tarihi, doğum saati, doğum yeri, erişim anahtarı veya ham harita dosyası tutulmaz.
