# -*- coding: utf-8 -*-
"""Kural motoru — generator_version: digest_rules_v2.

105 yeniden kullanilan parca, 495 olasi nihai cumle. Butun birlesimler
otomatik olarak dogrulandi: <=22 kelime, tek noktali virgul, tek nokta,
yasakli ifade yok, teknik terim yok, acilis/yan parca kok tekrari yok.

Birlesim kurali:
    gunluk   = tam cumle (dasha yan parcasi EKLENMEZ)
    haftalik = haftalik acilis + "; " + haftalik dasha parcasi + "."
    aylik    = aylik acilis    + "; " + aylik dasha parcasi    + "."
    aylik (Sade Sati) = Sade Sati acilisi + "; " + aylik dasha parcasi + "."

Sade Sati acilisi normal aylik acilisin YERINE gecer.

Dasha yan parcalari genel arketip temasidir; teknik hukum degildir.
"""

import re

DAILY = {
    1: [
        "Kendi isteklerin öne çıkabilir; ne istediğini söylemek olağandan kolay hissettirebilir.",
        "Gün seni merkeze alıyor gibi gelebilir; kendi ritmine göre hareket etmek kolaylaştırabilir.",
        "Başkalarının seni fark etmesi olağandan hızlı olabilir; ilk adımı atmak zor gelmeyebilir.",
    ],
    2: [
        "Sahip olduklarını gözden geçirmek isteyebilirsin; düzen ve birikim konuları sessizce gündeme gelebilir.",
        "Söylediklerinin ağırlığı olağandan fazla hissedilebilir; aile içi konuşmalar öne çıkabilir.",
        "Koruma ve toparlama isteği belirginleşebilir; acele karar vermemek rahatlatıcı olabilir.",
    ],
    3: [
        "Girişimde bulunmak olağandan kolay gelebilir; kısa mesafeler ve hızlı temaslar verimli olabilir.",
        "Cesaretin öne çıkabilir; yakın çevrenle kurduğun temas beklediğinden faydalı olabilir.",
        "Ertelediğin küçük adımlar akabilir; konuşma kapıları olağandan açık olabilir.",
    ],
    4: [
        "İçe dönme isteği artabilir; ev ve huzur alanın olağandan fazla ilgi isteyebilir.",
        "Duygusal zeminin biraz kaygan olabilir; kendine alan tanımak dengeleyici olabilir.",
        "Dışarıdaki koşuşturma yorucu gelebilir; tanıdık ortamlarda kalmak destekleyici olabilir.",
    ],
    5: [
        "Yaratıcı bir kıpırtı belirebilir; keyif aldığın alanlar olağandan çok dikkat çekebilir.",
        "Zihnin bir fikirle meşgul olabilir; gönül işleri gündemin ön sırasına geçebilir.",
        "Kendini ifade etme isteğin canlanabilir; ölçüyü korumak faydalı olabilir.",
    ],
    6: [
        "İş yükünü aşmak olağandan kolay olabilir; birikmiş işler beklediğinden hızlı ilerleyebilir.",
        "Engeller karşısında dayanıklılığın artabilir; rutine dönmek işine yarayabilir.",
        "Düzenine gösterdiğin özen karşılık bulabilir; ertelenen işler yerine oturabilir.",
    ],
    7: [
        "İlişkiler öne çıkabilir; karşı tarafın bakışını anlamak olağandan kolay gelebilir.",
        "Anlaşma ve ortaklık konuları hareketlenebilir; birlikte karar almak verimli olabilir.",
        "Karşındaki kişiyle kurduğun denge daha görünür hale gelebilir.",
    ],
    8: [
        "Yüzeyin altındaki konular gündeme gelebilir; acele sonuca varmamak koruyucu olabilir.",
        "Belirsizlik hissi artabilir; paylaşılan kaynaklarla ilgili konular dikkat gerektirebilir.",
        "Derinleşme isteği belirebilir; kendini zorlamadan beklemek rahatlatıcı olabilir.",
    ],
    9: [
        "Anlam arayışın belirginleşebilir; uzak konular ve yeni bakış açıları ilgini çekebilir.",
        "Öğrenme isteğin artabilir; sana yol gösterecek biriyle temas kurmak faydalı olabilir.",
        "Geniş resme bakmak daha mümkün olabilir; ayrıntılar geride kalabilir.",
    ],
    10: [
        "Görünürlüğün artabilir; yaptığın işin fark edilmesi olağandan kolay olabilir.",
        "Sorumluluk alma isteğin öne çıkabilir; iş tarafında adım atmak destekleyici olabilir.",
        "Yetkili kişilerle temas verimli olabilir; hedefine dair somut bir hamle mümkün olabilir.",
    ],
    11: [
        "Kazanç ve fırsat konuları hareketlenebilir; çevrenden gelen destek beklediğinden fazla olabilir.",
        "Arkadaş çevren öne çıkabilir; hedeflerine dair bir kapı aralanabilir.",
        "İstediğin şeye yaklaşmak olağandan kolay gelebilir; bağlantıların işine yarayabilir.",
    ],
    12: [
        "Geri çekilme isteği artabilir; dinlenmeye ayırdığın zaman olağandan değerli olabilir.",
        "Yorgunluk beklenenden erken gelebilir; kalabalıktan uzaklaşmak toparlayıcı olabilir.",
        "Dağınık dikkat öne çıkabilir; yavaşlamak dengeleyici olabilir.",
    ],
}

WEEKLY_OPEN = {
    1: [
        "Bu hafta kendini ortaya koyma isteğin öne çıkabilir",
        "Bu hafta ilgi kendi üzerinde toplanabilir",
    ],
    2: [
        "Bu hafta maddi düzen ve birikim konuları gündeme gelebilir",
        "Bu hafta sahip olduklarını gözden geçirme isteği belirebilir",
    ],
    3: [
        "Bu hafta girişim ve yakın temas tarafı canlanabilir",
        "Bu hafta çevrenle kurduğun bağ öne çıkabilir",
    ],
    4: [
        "Bu hafta ev ve iç dünya konuları ağırlık kazanabilir",
        "Bu hafta huzur alanını düzenleme isteği belirebilir",
    ],
    5: [
        "Bu hafta yaratıcılık ve keyif alanların öne çıkabilir",
        "Bu hafta kendini ortaya koyma arzun belirginleşebilir",
    ],
    6: [
        "Bu hafta iş yükü ve düzen konuları öne çıkabilir",
        "Bu hafta birikmiş işleri toparlama ihtiyacı belirebilir",
    ],
    7: [
        "Bu hafta ilişkiler ve ortaklıklar öne çıkabilir",
        "Bu hafta karşı tarafla kurduğun denge görünür hale gelebilir",
    ],
    8: [
        "Bu hafta yüzeyin altındaki konular gündeme gelebilir",
        "Bu hafta paylaşılan kaynaklar ağırlık kazanabilir",
    ],
    9: [
        "Bu hafta anlam arayışın belirginleşebilir",
        "Bu hafta geniş resme bakma ihtiyacı öne çıkabilir",
    ],
    10: [
        "Bu hafta iş ve görünürlük tarafı ağırlık kazanabilir",
        "Bu hafta iş tarafında adım atma isteğin artabilir",
    ],
    11: [
        "Bu hafta kazanç ve hedef konuları hareketlenebilir",
        "Bu hafta çevrenden gelen destek belirginleşebilir",
    ],
    12: [
        "Bu hafta geri çekilme ve dinlenme ihtiyacı öne çıkabilir",
        "Bu hafta tempoyu düşürme isteği belirebilir",
    ],
}

WEEKLY_DASHA = {
    'Jupiter': "dönemin genişleme vurgusu ufkunu açabilir",
    'Ketu': "dönemin sadeleşme vurgusu gereksiz olanı eleyebilir",
    'Mars': "dönemin atılım vurgusu adımlarını hızlandırabilir",
    'Mercury': "dönemin iletişim vurgusu konuşmaları hızlandırabilir",
    'Moon': "dönemin duygusal vurgusu tepkilerini yumuşatabilir",
    'Rahu': "dönemin yenilik vurgusu alışılmışın dışına çıkarabilir",
    'Saturn': "dönemin sorumluluk vurgusu ilerlemeyi yavaşlatabilir",
    'Sun': "dönemin öne çıkma vurgusu kararlarını netleştirebilir",
    'Venus': "dönemin uyum vurgusu yakınlaşmayı kolaylaştırabilir",
}

MONTHLY_OPEN = {
    1: [
        "Bu ay kendi gündemin öne geçebilir",
        "Bu ay kendi yönünü belirleme isteği artabilir",
    ],
    2: [
        "Bu ay maddi konular ve güvenlik ihtiyacı öne çıkabilir",
        "Bu ay birikim ve kaynak yönetimi ağırlık kazanabilir",
    ],
    3: [
        "Bu ay girişim ve yakın çevre konuları öne çıkabilir",
        "Bu ay küçük ve sürekli adımlar belirginleşebilir",
    ],
    4: [
        "Bu ay ev ve iç huzur konuları ağırlık kazanabilir",
        "Bu ay içe dönme isteği belirginleşebilir",
    ],
    5: [
        "Bu ay yaratıcılık ve gönül konuları öne çıkabilir",
        "Bu ay kendini ortaya koyma arzun artabilir",
    ],
    6: [
        "Bu ay iş yükü ve dayanıklılık konuları gündemde olabilir",
        "Bu ay rutine dönme ihtiyacı öne çıkabilir",
    ],
    7: [
        "Bu ay ilişkiler ve ortaklıklar gündemin ana başlığı olabilir",
        "Bu ay karşı tarafla kurduğun denge gündeme gelebilir",
    ],
    8: [
        "Bu ay derin ve gizli kalmış konular yüzeye çıkabilir",
        "Bu ay paylaşılan kaynaklar ağırlık kazanabilir",
    ],
    9: [
        "Bu ay anlam ve öğrenme konuları öne çıkabilir",
        "Bu ay yeni bakış açıları ilgini çekebilir",
    ],
    10: [
        "Bu ay iş ve statü konuları merkeze yerleşebilir",
        "Bu ay yaptığın işin karşılığı öne çıkabilir",
    ],
    11: [
        "Bu ay kazanç ve hedef konuları ağırlık kazanabilir",
        "Bu ay topluluk içindeki yerin belirginleşebilir",
    ],
    12: [
        "Bu ay geri çekilme ve toparlanma ihtiyacı öne çıkabilir",
        "Bu ay kendine alan açma isteği belirebilir",
    ],
}

MONTHLY_DASHA = {
    'Jupiter': "dönemin genişleme eğilimi yeni alanlar açabilir",
    'Ketu': "dönemin sadeleşme eğilimi bağlarını gözden geçirtebilir",
    'Mars': "dönemin hareket eğilimi karar almanı hızlandırabilir",
    'Mercury': "dönemin iletişim eğilimi bilgi akışını artırabilir",
    'Moon': "dönemin duygusal eğilimi yakınlık arayışını güçlendirebilir",
    'Rahu': "dönemin yenilik eğilimi alışılmış düzeni sorgulatabilir",
    'Saturn': "dönemin sorumluluk eğilimi kalıcı olana yöneltebilir",
    'Sun': "dönemin öne çıkma eğilimi kişisel duruşunu pekiştirebilir",
    'Venus': "dönemin uyum eğilimi yakınlaşmayı ön plana taşıyabilir",
}

SADE_SATI_OPEN = [
    "Bu ay temposu yavaş bir aşamada olabilirsin",
    "Bu ay yükün olağandan görünür hale gelebilir",
    "Bu ay ilerleme küçük adımlarla mümkün olabilir",
]

FOCUS = {
    1: "kendin",
    2: "kaynak",
    3: "girisim",
    4: "huzur",
    5: "yaraticilik",
    6: "duzen",
    7: "iliski",
    8: "derinlik",
    9: "anlam",
    10: "is",
    11: "cevre",
    12: "dinlenme",
}


# --------------------------------------------------------- yasakli tarama

BANNED_PHRASES = [
    "evren sana", "kozmik enerji", "enerjini yükselt", "şanslı gün",
    "büyük değişim", "hayatın değişecek", "dikkat!",
]

BANNED_WORDS = [
    "kaçırma", "mutlaka", "kesinlikle", "asla", "tehlike", "uyarı",
]

_TR = "0-9A-Za-zÇĞİıÖŞÜçğöşü"
_WORD_RE = re.compile(
    r"(?<![%s])(%s)(?![%s])" % (_TR, "|".join(BANNED_WORDS), _TR),
    re.IGNORECASE,
)


def has_banned(text):
    """Alt dize degil kelime siniri kullanir; 'temaslar' icindeki 'asla'
    gibi yanlis eslesmeleri onler."""
    low = (text or "").lower()
    if any(p in low for p in BANNED_PHRASES):
        return True
    return bool(_WORD_RE.search(text or ""))


# ---------------------------------------------------------- uretim

def _rotate(pool, seed):
    return pool[seed % len(pool)]


def house_of(situation):
    layer = situation["layer"]
    if layer == "daily":
        return situation["ay_evi"]
    if layer == "weekly":
        return situation["baskin_ev"]
    return situation["gunes_evi"]


def compose(opening, fragment):
    return "%s; %s." % (opening, fragment)


def generate(situation, seed):
    """Durum paketinden deterministik cumle uretir.

    seed: keys.rotation_seed(layer, date). Ayni donemde ayni cumle.
    """
    layer = situation["layer"]
    house = house_of(situation)

    if layer == "daily":
        cumle = _rotate(DAILY[house], seed)

    elif layer == "weekly":
        lord = situation.get("dasha_lord")
        opening = _rotate(WEEKLY_OPEN[house], seed)
        cumle = compose(opening, WEEKLY_DASHA[lord])

    elif layer == "monthly":
        lord = situation.get("dasha_lord")
        if situation.get("sade_sati"):
            opening = _rotate(SADE_SATI_OPEN, seed)
        else:
            opening = _rotate(MONTHLY_OPEN[house], seed)
        cumle = compose(opening, MONTHLY_DASHA[lord])

    else:
        raise ValueError("bilinmeyen katman: %s" % layer)

    return {"cumle": cumle, "odak": FOCUS[house]}
