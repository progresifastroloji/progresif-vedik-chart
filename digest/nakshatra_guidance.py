"""Günlük Ay nakşatrası için sınırlı, düzenlenebilir rehberlik tohumları.

Bu tablo hesap yapmaz ve tek başına hüküm üretmez. Nakşatranın doğrulanmış
adı/padası ile günün kişisel odağını aynı paragrafta somut bir gözlem,
uygulanabilir bir adım ve dikkat noktasıyla buluşturmak için yazıcıya sınır
sağlar. Metinler kesin gelecek iddiası değil, seçimi kullanıcıda bırakan
gözlem dilidir.
"""


NAKSHATRA_GUIDANCE = {
    "Ashwini": {"theme": "başlatma, hız ve ilk adım", "action": "bekleyen işi başlatacak en küçük adımı seç", "watch": "hız uğruna ayrıntıyı atlama"},
    "Bharani": {"theme": "yük, sınır ve sorumluluk", "action": "taşıdığın yükleri ayırıp bir sınır cümlesi kur", "watch": "başkasının yükünü kendi görevin sanma"},
    "Krittika": {"theme": "ayıklama, netlik ve seçim", "action": "günün önceliğini keskin biçimde belirle", "watch": "netliği kırıcı bir tona dönüştürme"},
    "Rohini": {"theme": "besleme, üretme ve istikrar", "action": "sürdürülebilir bir işi küçük bir ritme bağla", "watch": "rahatlığı erteleme bahanesi yapma"},
    "Mrigashira": {"theme": "arama, merak ve seçenekleri yoklama", "action": "iki seçeneği karşılaştırıp birini denemeye al", "watch": "sonsuz araştırmada kalma"},
    "Ardra": {"theme": "yoğunluğu çözme ve gerçeği görme", "action": "zor konuyu parçalara ayırıp adını açıkça koy", "watch": "ilk duygusal tepkiyle karar verme"},
    "Punarvasu": {"theme": "yenileme, dönüş ve sadeleşme", "action": "işe yarayan bir alışkanlığa geri dön", "watch": "eski yöntemi neden bıraktığını unutma"},
    "Pushya": {"theme": "destek, yapı ve besleyici düzen", "action": "seni taşıyan bir destek veya rutin belirle", "watch": "destek vermeyi kendini tüketmeye çevirme"},
    "Ashlesha": {"theme": "bağın alt katmanı ve sınır", "action": "söylenmeyen ihtiyacı sakin bir soruyla aç", "watch": "ima ve kuşkuyu kanıt yerine koyma"},
    "Magha": {"theme": "kökler, itibar ve yetki", "action": "hangi değeri sürdürmek istediğini yaz", "watch": "geçmişin beklentisini bugünün seçimi sanma"},
    "Purva Phalguni": {"theme": "keyif, yaratım ve dinlenme", "action": "üretim ile dinlenme için ayrı zaman aç", "watch": "anlık keyif uğruna uzun vadeli dengeyi bozma"},
    "Uttara Phalguni": {"theme": "söz, dayanışma ve sürdürülebilir bağ", "action": "bir anlaşmanın kapsamını ve sınırını netleştir", "watch": "uyumu korumak için ihtiyacını gizleme"},
    "Hasta": {"theme": "beceri, düzenleme ve tamamlanabilir iş", "action": "elinin değdiği tek bir işi sonuna kadar götür", "watch": "her şeyi kontrol etmeye çalışma"},
    "Chitra": {"theme": "tasarım, görünürlük ve ayrıntı", "action": "dağınık fikri görünür bir taslağa dönüştür", "watch": "görüntüyü özün önüne koyma"},
    "Swati": {"theme": "bağımsızlık, esneklik ve kendi yönü", "action": "başkasının temposundan ayrışan bir karar ver", "watch": "özgürlük adına bağlantıyı koparma"},
    "Vishakha": {"theme": "hedef, odak ve kararlılık", "action": "tek hedef seçip ilerlemeyi ölçülebilir kıl", "watch": "sonuca kilitlenip süreci ihmal etme"},
    "Anuradha": {"theme": "sadakat, işbirliği ve ritim", "action": "güvendiğin biriyle rol paylaşımını netleştir", "watch": "sadakati tek taraflı çabaya dönüştürme"},
    "Jyeshtha": {"theme": "sorumluluk, koruma ve ölçü", "action": "koruman gereken sınırı açıkça belirt", "watch": "her sorumluluğu tek başına üstlenme"},
    "Mula": {"theme": "kök nedeni araştırma ve yeniden kurma", "action": "tekrarlayan sorunun kök nedenini yaz", "watch": "söküp yerine koymayı erteleme"},
    "Purva Ashadha": {"theme": "ilke, ikna ve cesaret", "action": "savunduğun ilkeyi somut bir davranışa çevir", "watch": "iknayı baskıya dönüştürme"},
    "Uttara Ashadha": {"theme": "kalıcı hedef, doğruluk ve ortak sorumluluk", "action": "uzun vadeli hedef için bir sorumluluğu kesinleştir", "watch": "haklılığı esnekliğin önüne koyma"},
    "Shravana": {"theme": "dinleme, öğrenme ve doğru aktarım", "action": "önce dinleyip sonra tek cümleyle özetle", "watch": "duyduğunu varsayımla tamamlamama"},
    "Dhanishta": {"theme": "ritim, kaynakları birleştirme ve ortak hedef", "action": "öncelik sırası çıkarıp kaynaklarını tek hedefte topla", "watch": "aynı anda çok şeye yetişmeye çalışma"},
    "Shatabhisha": {"theme": "mesafe, gözlem ve onarım", "action": "tepki vermeden önce gözlem için kısa bir alan aç", "watch": "mesafeyi kopuş gibi kullanma"},
    "Purva Bhadrapada": {"theme": "derin inanç, adanma ve sınır", "action": "seni gerçekten bağlayan nedeni bir cümleyle yaz", "watch": "yoğunluğu değişmez hükme çevirme"},
    "Uttara Bhadrapada": {"theme": "sabır, derinlik ve sürdürülebilirlik", "action": "yavaş ilerleyen işi dayanabileceğin bir ritme koy", "watch": "beklemeyi eylemsizlik sanma"},
    "Revati": {"theme": "tamamlama, geçiş ve koruyucu yön", "action": "açık bir işi kapatıp sonraki geçişi planla", "watch": "herkesi taşırken kendi yönünü kaybetme"},
}


FOCUS_GUIDANCE = {
    "kendin": {"topic": "sınır ve öz-ifade", "area": "kişisel duruş", "action": "bugün tek bir önceliğini açıkça ifade et", "watch": "başkasının beklentisini kendi ihtiyacın sanma"},
    "kaynak": {"topic": "kaynak ve güven", "area": "para ve sahip oldukların", "action": "kaynaklarını etkileyen tek bir kararı gözden geçir", "watch": "kısa rahatlık için uzun vadeli güveni zedeleme"},
    "girişim": {"topic": "iletişim ve ilk adım", "area": "yakın çevre ve hareket", "action": "bekleyen konuşmayı kısa ve net bir cümleyle başlat", "watch": "cevap hızını anlam yerine koyma"},
    "huzur": {"topic": "iç güven ve ev düzeni", "area": "ev ve duygusal zemin", "action": "sana sakin alan açan tek bir düzenleme yap", "watch": "yakınlarının ritmini kendi ihtiyacının önüne koyma"},
    "yaratıcılık": {"topic": "üretim ve neşe", "area": "yaratıcılık ve keyif", "action": "fikrini görünür kılan küçük bir çıktı üret", "watch": "onay beklerken üretimi erteleme"},
    "düzen": {"topic": "rutin ve sorumluluk", "area": "günlük işleyiş", "action": "günün iki gerçek önceliğini takvimine yerleştir", "watch": "her talebi aynı anda çözmeye çalışma"},
    "ilişki": {"topic": "karşılıklılık ve sınır", "area": "yakın ilişkiler", "action": "ihtiyacını ve verebileceğin desteği açıkça söyle", "watch": "dengeyi tek başına taşımaya çalışma"},
    "derinlik": {"topic": "paylaşım ve güven", "area": "ortak kaynaklar ve mahremiyet", "action": "paylaşacağın bilginin sınırını önceden belirle", "watch": "belirsizliği acele itiraf veya kararla kapatma"},
    "anlam": {"topic": "öğrenme ve yön", "area": "inançlar ve ufuk", "action": "bakışını genişleten tek bir soruya zaman ayır", "watch": "tek doğru arayışıyla merakı kapatma"},
    "iş": {"topic": "öncelik ve görünür sorumluluk", "area": "kariyer ve görevler", "action": "sonucu görünür kılan bir işi önce tamamla", "watch": "hızlı görünmek için kapasiteni aşan söz verme"},
    "çevre": {"topic": "destek ve topluluk", "area": "arkadaşlar ve bağlantılar", "action": "destek aldığın veya vereceğin kişiyi netleştir", "watch": "gruba uyum için kendi sınırını silme"},
    "dinlenme": {"topic": "kapanış ve toparlanma", "area": "dinlenme ve içe dönüş", "action": "günü kapatacak gerçek bir mola planla", "watch": "sessizliği yeni bir endişe listesiyle doldurma"},
}
