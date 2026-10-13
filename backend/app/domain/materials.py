MATERIAL_FAMILIES={
"Düşük / Orta Karbonlu Çelik":{"status":"supported"},
"AHSS / UHSS / PHS":{"status":"limited"},
"Galvanizli / Kaplamalı Çelik":{"status":"limited"},
"Paslanmaz Çelik":{"status":"limited"},
"Alüminyum Alaşımları":{"status":"reference_only"},
"Süper Alaşımlar":{"status":"unsupported"},
"Karma Malzeme":{"status":"unsupported"}}
MATERIAL_SUBCLASSES={
"Düşük / Orta Karbonlu Çelik":["Düşük karbonlu çelik","Orta karbonlu çelik"],
"AHSS / UHSS / PHS":["DP600","DP780","TRIP","Bor çeliği / PHS"],
"Galvanizli / Kaplamalı Çelik":["GI","GA","Zn kaplı"],
"Paslanmaz Çelik":["AISI 304","AISI 202","Ferritik 430"],
"Alüminyum Alaşımları":["AA5182","2014-O","5xxx serisi","6xxx serisi"],
"Süper Alaşımlar":["Nikel bazlı","Kobalt bazlı"],
"Karma Malzeme":["Çelik + alüminyum","Kaplamalı + kaplamasız çelik"]}

# Unambiguous English aliases → Turkish canonical key.
# "Steel" alone is intentionally absent: it is ambiguous (mild, coated, or AHSS).
_MATERIAL_FAMILY_ALIASES: dict = {
    "mild steel":                  "Düşük / Orta Karbonlu Çelik",
    "low carbon steel":            "Düşük / Orta Karbonlu Çelik",
    "low/medium carbon steel":     "Düşük / Orta Karbonlu Çelik",
    "mild/medium carbon steel":    "Düşük / Orta Karbonlu Çelik",
    "ahss":                        "AHSS / UHSS / PHS",
    "uhss":                        "AHSS / UHSS / PHS",
    "phs":                         "AHSS / UHSS / PHS",
    "ahss / uhss / phs":           "AHSS / UHSS / PHS",
    "galvanized steel":            "Galvanizli / Kaplamalı Çelik",
    "galvanized":                  "Galvanizli / Kaplamalı Çelik",
    "galvanised steel":            "Galvanizli / Kaplamalı Çelik",
    "galvanised":                  "Galvanizli / Kaplamalı Çelik",
    "coated steel":                "Galvanizli / Kaplamalı Çelik",
    "zinc coated":                 "Galvanizli / Kaplamalı Çelik",
    "stainless steel":             "Paslanmaz Çelik",
    "stainless":                   "Paslanmaz Çelik",
    "aluminum alloys":             "Alüminyum Alaşımları",
    "aluminium alloys":            "Alüminyum Alaşımları",
    "aluminum":                    "Alüminyum Alaşımları",
    "aluminium":                   "Alüminyum Alaşımları",
    "superalloy":                  "Süper Alaşımlar",
    "superalloys":                 "Süper Alaşımlar",
    "super alloy":                 "Süper Alaşımlar",
    "mixed":                       "Karma Malzeme",
    "mixed material":              "Karma Malzeme",
    "dissimilar":                  "Karma Malzeme",
}


def resolve_material_family(value: str) -> str:
    """Return the canonical Turkish key for *value*, or raise ValueError.

    Accepts exact Turkish canonical keys and unambiguous English aliases
    (case-insensitive, leading/trailing whitespace stripped).
    Ambiguous values such as bare 'Steel' are rejected.
    Never silently substitutes a default material.
    """
    stripped = value.strip()
    if stripped in MATERIAL_FAMILIES:
        return stripped
    canonical = _MATERIAL_FAMILY_ALIASES.get(stripped.lower())
    if canonical is None:
        raise ValueError(
            f"UNSUPPORTED_MATERIAL_FAMILY: '{value}'. "
            f"Supported: {list(MATERIAL_FAMILIES.keys())}"
        )
    return canonical
