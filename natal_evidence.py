"""Character meanings projected from VedicAI's existing, curated library."""
import json
import unicodedata
from functools import lru_cache
from pathlib import Path


def _fold(value):
    return "".join(c.lower() for c in unicodedata.normalize("NFKD", str(value or "")) if c.isascii() and c.isalnum())


@lru_cache(maxsize=1)
def _library():
    return json.loads((Path(__file__).parent / "data/nakshatra-character.json").read_text(encoding="utf-8"))


def nakshatra_character(nakshatra, planet=None):
    nakshatra = nakshatra or {}
    library = _library()
    wanted = _fold(nakshatra.get("name"))
    entry = next((item for item in library["entries"] if wanted in {_fold(item["latin"]), _fold(item["display"])}), None)
    if not entry:
        return {"status": "not_available", "reason": "Nakşatra mevcut anlam kütüphanesinde eşleşmedi."}
    labels = {"Sun": "Güneş", "Moon": "Ay", "Mercury": "Merkür", "Venus": "Venüs", "Jupiter": "Jüpiter", "Saturn": "Satürn"}
    label = labels.get(planet, planet)
    planet_meaning = next((line.split(":", 1)[1].strip() for line in entry["planets"].splitlines() if label and line.startswith(label + ":")), None)
    pada = nakshatra.get("pada")
    pada_meaning = next((line for line in entry["padas"].splitlines() if line.startswith(f"P{pada} ")), None)
    return {
        "status": "available", "headline": entry["headline"], "meaning": entry["meaning"],
        "pada_meaning": pada_meaning, "planet_meaning": planet_meaning,
        "source": library["source"], "source_sha256": library["source_sha256"],
        "scope": "Genel anlam; ev, yöneticilik, drishti, gezegen gücü ve D9 ile kişiselleştirilir.",
    }
