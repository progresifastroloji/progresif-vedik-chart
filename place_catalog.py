"""GeoNames tabanli dogum yeri katalogu olusturma ve arama yardimcilari."""

from __future__ import annotations

import re
import sqlite3
import unicodedata
import zipfile
from contextlib import closing
from pathlib import Path


GEONAMES_COLUMNS = (
    "geoname_id",
    "name",
    "ascii_name",
    "alternate_names",
    "latitude",
    "longitude",
    "feature_class",
    "feature_code",
    "country_code",
    "cc2",
    "admin1_code",
    "admin2_code",
    "admin3_code",
    "admin4_code",
    "population",
    "elevation",
    "dem",
    "timezone_id",
    "modification_date",
)


class PlaceCatalogUnavailable(RuntimeError):
    """Yer katalogu henuz olusturulmadi veya okunamiyor."""


def normalize_place_text(value: str) -> str:
    """Aramayi buyuk/kucuk harf ve aksan farklarina dayanikli hale getirir."""
    decomposed = unicodedata.normalize("NFKD", str(value or "").casefold())
    without_marks = "".join(char for char in decomposed if not unicodedata.combining(char))
    return " ".join(without_marks.replace("ı", "i").split())


def _load_country_names(path: Path | None) -> dict[str, str]:
    names: dict[str, str] = {}
    if path is None:
        return names
    with path.open("r", encoding="utf-8") as source:
        for line in source:
            if not line.strip() or line.startswith("#"):
                continue
            fields = line.rstrip("\n").split("\t")
            if len(fields) >= 5:
                names[fields[0]] = fields[4]
    return names


def _load_admin1_names(path: Path | None) -> dict[str, str]:
    names: dict[str, str] = {}
    if path is None:
        return names
    with path.open("r", encoding="utf-8") as source:
        for line in source:
            fields = line.rstrip("\n").split("\t")
            if len(fields) >= 2:
                names[fields[0]] = fields[1]
    return names


def _open_cities_source(path: Path):
    if path.suffix.casefold() == ".zip":
        archive = zipfile.ZipFile(path)
        members = [name for name in archive.namelist() if name.endswith(".txt")]
        if len(members) != 1:
            archive.close()
            raise ValueError("GeoNames ZIP icinde tek bir sehir TXT dosyasi bekleniyor")
        return archive, archive.open(members[0], "r")
    return None, path.open("rb")


def build_places_database(
    cities_path: str | Path,
    database_path: str | Path,
    *,
    country_info_path: str | Path | None = None,
    admin1_codes_path: str | Path | None = None,
    dataset_name: str = "cities500",
) -> int:
    """GeoNames TSV/ZIP dosyasini aramaya hazir bir SQLite kataloguna donusturur."""
    cities_path = Path(cities_path)
    database_path = Path(database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    country_names = _load_country_names(Path(country_info_path) if country_info_path else None)
    admin1_names = _load_admin1_names(Path(admin1_codes_path) if admin1_codes_path else None)

    if database_path.exists():
        database_path.unlink()

    archive, binary_source = _open_cities_source(cities_path)
    inserted = 0
    try:
        with closing(sqlite3.connect(database_path)) as conn:
            conn.executescript(
                """
                PRAGMA journal_mode = OFF;
                PRAGMA synchronous = OFF;
                CREATE TABLE places (
                    geoname_id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    ascii_name TEXT NOT NULL,
                    country_code TEXT NOT NULL,
                    country_name TEXT NOT NULL,
                    admin1_code TEXT,
                    admin1_name TEXT,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    timezone_id TEXT NOT NULL,
                    population INTEGER NOT NULL,
                    feature_code TEXT NOT NULL,
                    modification_date TEXT NOT NULL,
                    search_name TEXT NOT NULL,
                    search_aliases TEXT NOT NULL
                );
                CREATE VIRTUAL TABLE places_fts USING fts5(
                    geoname_id UNINDEXED,
                    search_name,
                    search_aliases,
                    tokenize = 'unicode61 remove_diacritics 2'
                );
                """
            )
            batch: list[tuple] = []
            for raw_line in binary_source:
                fields = raw_line.decode("utf-8").rstrip("\n").split("\t")
                if len(fields) != len(GEONAMES_COLUMNS):
                    continue
                row = dict(zip(GEONAMES_COLUMNS, fields))
                country_code = row["country_code"]
                admin1_key = f"{country_code}.{row['admin1_code']}"
                searchable_names = [row["name"], row["ascii_name"]]
                searchable_names.extend(row["alternate_names"].split(","))
                normalized_aliases = ",".join(
                    dict.fromkeys(
                        normalized
                        for value in searchable_names
                        if (normalized := normalize_place_text(value))
                    )
                )
                batch.append(
                    (
                        int(row["geoname_id"]),
                        row["name"],
                        row["ascii_name"],
                        country_code,
                        country_names.get(country_code, country_code),
                        row["admin1_code"] or None,
                        admin1_names.get(admin1_key),
                        float(row["latitude"]),
                        float(row["longitude"]),
                        row["timezone_id"],
                        int(row["population"] or 0),
                        row["feature_code"],
                        row["modification_date"],
                        normalize_place_text(row["name"]),
                        normalized_aliases,
                    )
                )
                if len(batch) >= 2000:
                    inserted += _insert_batch(conn, batch)
                    batch.clear()
            if batch:
                inserted += _insert_batch(conn, batch)

            conn.executescript(
                """
                CREATE INDEX idx_places_country ON places(country_code);
                CREATE INDEX idx_places_search_name ON places(search_name);
                CREATE TABLE catalog_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                """
            )
            conn.executemany(
                "INSERT INTO catalog_metadata(key, value) VALUES (?, ?)",
                (
                    ("source", "GeoNames"),
                    ("license", "CC BY 4.0"),
                    ("dataset", dataset_name),
                    ("place_count", str(inserted)),
                ),
            )
            conn.commit()
    finally:
        binary_source.close()
        if archive is not None:
            archive.close()
    return inserted


def _insert_batch(conn: sqlite3.Connection, batch: list[tuple]) -> int:
    conn.executemany(
        """
        INSERT INTO places (
            geoname_id, name, ascii_name, country_code, country_name,
            admin1_code, admin1_name, latitude, longitude, timezone_id,
            population, feature_code, modification_date, search_name, search_aliases
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        batch,
    )
    conn.executemany(
        "INSERT INTO places_fts(geoname_id, search_name, search_aliases) VALUES (?, ?, ?)",
        ((row[0], row[13], row[14]) for row in batch),
    )
    return len(batch)


def search_places(
    database_path: str | Path,
    query: str,
    *,
    country_code: str | None = None,
    limit: int = 8,
) -> list[dict]:
    """Yer adini on ek ve alternatif adlar uzerinden arar."""
    database_path = Path(database_path)
    if not database_path.is_file():
        raise PlaceCatalogUnavailable(f"Dogum yeri katalogu bulunamadi: {database_path}")

    normalized = normalize_place_text(query)
    if len(normalized) > 100:
        raise ValueError("Dogum yeri aramasi en fazla 100 karakter olmali")
    tokens = re.findall(r"[\w]+", normalized, flags=re.UNICODE)
    if not tokens or len(normalized) < 2:
        raise ValueError("Dogum yeri aramasi en az 2 karakter olmali")
    match_query = " AND ".join(f'"{token}"*' for token in tokens[:6])
    country_code = str(country_code or "").strip().upper() or None
    if country_code and not re.fullmatch(r"[A-Z]{2}", country_code):
        raise ValueError("country iki harfli ulke kodu olmali")
    limit = max(1, min(int(limit), 20))

    sql = """
        SELECT p.geoname_id, p.name, p.country_code, p.country_name,
               p.admin1_code, p.admin1_name, p.latitude, p.longitude,
               p.timezone_id, p.population, p.feature_code
        FROM places_fts
        JOIN places p ON p.geoname_id = places_fts.geoname_id
        WHERE places_fts MATCH ?
    """
    params: list[object] = [match_query]
    if country_code:
        sql += " AND p.country_code = ?"
        params.append(country_code)
    sql += """
        ORDER BY
            CASE
                WHEN p.search_name = ? THEN 0
                WHEN (',' || p.search_aliases || ',') LIKE ? THEN 1
                WHEN p.search_name LIKE ? THEN 2
                ELSE 3
            END,
            bm25(places_fts),
            p.population DESC
        LIMIT ?
    """
    params.extend((normalized, f"%,{normalized},%", f"{normalized}%", limit))

    try:
        uri = f"file:{database_path.resolve()}?mode=ro"
        with closing(sqlite3.connect(uri, uri=True)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(sql, params).fetchall()
    except sqlite3.Error as exc:
        raise PlaceCatalogUnavailable("Dogum yeri katalogu okunamadi") from exc

    return [
        {
            "place_id": str(row["geoname_id"]),
            "name": row["name"],
            "label": _place_label(row),
            "country_code": row["country_code"],
            "country_name": row["country_name"],
            "admin1_code": row["admin1_code"],
            "admin1_name": row["admin1_name"],
            "latitude": row["latitude"],
            "longitude": row["longitude"],
            "timezone_id": row["timezone_id"],
            "population": row["population"],
            "feature_code": row["feature_code"],
        }
        for row in rows
    ]


def _place_label(row: sqlite3.Row) -> str:
    parts = [row["name"]]
    if row["admin1_name"] and row["admin1_name"] != row["name"]:
        parts.append(row["admin1_name"])
    parts.append(row["country_name"])
    return ", ".join(parts)
