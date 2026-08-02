# Vedik metodoloji adayları — kontrollü beta kopyası

Bu klasör, `vedicai-web/methodologies` içindeki üç adayın 2026-08-02 tarihli birebir sunucu kopyasını taşır.

- Dosyalar yalnız `POST /api/v2/beta/chat/compare` kontrollü karşılaştırmasında kullanılır.
- Üçünün de statüsü `candidate` olarak kalır; hiçbiri otomatik seçilmez veya final ilan edilmez.
- `methodology_orchestrator.py`, kimlik/sürüm/statü ve SHA-256 değerini çağrıdan önce doğrular; fark varsa model çağrısı yapmadan güvenli biçimde durur.
- Her aday aynı küçültülmüş teknik kanıt paketini ayrı bir Vertex isteğinde alır. Aday belgeleri tek prompt içinde karıştırılmaz.
- Kaynak SHA-256 değerleri:
  - `vedic-classical-strict-v1.md`: `f38a9dfb3f6954f46c2e8b2b5863aaeecb7983aef709a3a5e2b644ec0a78cd1d`
  - `vedic-comprehensive-deep-v1.md`: `f6d9a85e35029d096d2cc681399a5620d9aece2fa4b7647b186b77d759fa7d88`
  - `vedic-ai-application-v1.md`: `b89d8db41983c9a8589b9cd33a8a14eb2cf64bac2cca65334493c2f9e1a8147b`
