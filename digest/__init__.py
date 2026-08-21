"""daily_digest — gunluk/haftalik/aylik tek cumle uretimi.

Mevcut API'ye dokunmaz. Astrolojik kaynak yalniz
vedic_chart.calculate_chart'tir; HTTP ic cagrisi ve kukla dogum
verisi kullanilmaz.

generator_version: digest_rules_v2
"""

from .keys import GENERATOR_VERSION, SCHEMA_VERSION
from .routes import digest_bp
from .paid_routes import paid_digest_bp

__all__ = ["digest_bp", "paid_digest_bp", "GENERATOR_VERSION", "SCHEMA_VERSION"]
