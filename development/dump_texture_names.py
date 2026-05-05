"""
Dumps all texture filenames (without extension) from the TEXTURES folder
and generates a user-friendly display name for each.

Output: texture_names.txt (raw names) and texture_names_friendly.txt (name -> friendly)
"""

import os
import re
from pathlib import Path

TEXTURE_DIR = Path(__file__).parent.parent / "resources" / "editor" / "TEXTURES"

# ── Prefix → district / category label ────────────────────────────────────────
PREFIX_MAP = {
    "CT":  "Chinatown",
    "DT":  "Downtown",
    "H":   "Hills",
    "IND": "Industrial",
    "OT":  "Old Town",
    "R":   "Residential",
    "T":   "Town",
    "L":   "Landmark",
    "G":   "Generic",
    "VP":  "Vehicle Part",
    "VA":  "Vehicle Ambient",
    "FX":  "Effect",
    "SKY": "Sky",
    "REFL":"Reflection",
    "FXPT":"Particle",
    "RFWY":"Ramp/Freeway",
}

# ── Building type abbreviations ────────────────────────────────────────────────
BLDG_TYPE_MAP = {
    "APT":    "Apartment",
    "APT2":   "Apartment 2",
    "APT3":   "Apartment 3",
    "BNK":    "Bank",
    "BLDG":   "Building",
    "CLUB":   "Club",
    "CONDO":  "Condo",
    "DELI":   "Deli",
    "DINR":   "Diner",
    "DRUG":   "Drug Store",
    "FACT":   "Factory",
    "FOOD":   "Food Shop",
    "GUN":    "Gun Shop",
    "HOME":   "Home",
    "HOTEL":  "Hotel",
    "HOUSE":  "House",
    "HOUSE02":"House 2",
    "HOUSE03":"House 3",
    "INN":    "Inn",
    "LIQR":   "Liquor Store",
    "LIQUR":  "Liquor Store",
    "MALL":   "Mall",
    "MARKT":  "Market",
    "MOTEL":  "Motel",
    "OFFCE":  "Office",
    "OFFICE": "Office",
    "PAWN":   "Pawn Shop",
    "PIZZA":  "Pizza Shop",
    "PIZA":   "Pizza Shop",
    "PSTA":   "Pasta Shop",
    "SCOTT":  "Scott Building",
    "SHOP":   "Shop",
    "SKY":    "Skyscraper",
    "STOR":   "Store",
    "THETR":  "Theatre",
    "WOOD":   "Wood Building",
    "BAR":    "Bar",
    "UC":     "Under Construction",
    "O":      "Office",
    "R":      "Residential",
    "Y":      "Yellow Brick",
    "B":      "Blue",
    "G":      "Green",
}

# ── Surface / element type tokens ─────────────────────────────────────────────
SURFACE_MAP = {
    "BRICK":       "Brick",
    "BIRCK":       "Brick",        # typo in source
    "WIN":         "Window",
    "DOOR":        "Door",
    "TRIM":        "Trim",
    "WALL":        "Wall",
    "ROOF":        "Roof",
    "SIGN":        "Sign",
    "SIDE":        "Side",
    "AWNING":      "Awning",
    "AWNING1":     "Awning",
    "AWNING2":     "Awning",
    "BANNER":      "Banner",
    "BNR":         "Banner",
    "CLOCK":       "Clock",
    "CONCRETE":    "Concrete",
    "CRETE":       "Concrete",
    "ASPHALT":     "Asphalt",
    "ASPHALTLINES":"Asphalt Lines",
    "GRASS":       "Grass",
    "GRID":        "Grid",
    "GRIDWORK":    "Gridwork",
    "IBEAM":       "I-Beam",
    "INDENT":      "Indent",
    "INSIDE":      "Inside",
    "LIGHT":       "Light",
    "NEON":        "Neon",
    "ONING":       "Awning",       # typo for awning in source
    "RAIL":        "Rail",
    "RIVET":       "Rivet",
    "ROAD":        "Road",
    "ROCK":        "Rock",
    "RUST":        "Rust",
    "SDWLK":       "Sidewalk",
    "SIDING":      "Siding",
    "SLIDINGDOOR": "Sliding Door",
    "STEP":        "Step",
    "TARP":        "Tarp",
    "TIN":         "Tin",
    "TOP":         "Top",
    "TRACK":       "Track",
    "TRUCK":       "Truck",
    "TUN":         "Tunnel",
    "VENT":        "Vent",
    "WATER":       "Water",
    "WOOD":        "Wood",
    "WORK":        "Work",
    "TREE":        "Tree",
    "SNOW":        "Snow",
    "DIRT":        "Dirt",
    "GLASS":       "Glass",
    "FLOOR":       "Floor",
    "JERSEY":      "Jersey Barrier",
    "WALK":        "Walkway",
    "ALLEY":       "Alley",
    "POOL":        "Pool",
    "GARBAGE":     "Garbage",
    "TRASH":       "Trash",
    "MAIL":        "Mail Box",
    "POSTER":      "Poster",
    "ATM":         "ATM",
    "BOOTH":       "Booth",
    "SCORBD":      "Scoreboard",
    "STAT":        "Statue",
    "DUCK":        "Duck",
    "PAWN":        "Pawn",
    "CRAN":        "Crane",
    "STRCT":       "Structure",
    "MEDIABOX":    "Media Box",
    "RUBLE":       "Rubble",
    "SHIP":        "Ship",
    "FISH":        "Fish",
    "FIRE":        "Fire",
    "CLUB":        "Club",
    "SIGNPROP":    "Sign Prop",
    "CD":          "CD Store",
    "DEPT":        "Department Store",
    "DRUG":        "Drug Store",
    "BARRICADE":   "Barricade",
    "CAUTION":     "Caution",
    "BOX":         "Box",
    "CARDBORDBOX": "Cardboard Box",
    "DMPSTRFRNT":  "Dumpster Front",
    "METER":       "Meter",
    "NEWS":        "Newsstand",
    "PHONE":       "Phone",
    "POLE":        "Pole",
    "USFLAG":      "US Flag",
    "BLACK":       "Black",
    "BLACKLINE":   "Black Line",
    "GRAY":        "Gray",
    "BRN":         "Brown",
    "RUF":         "Roof",
    "LMMALL":      "Lakeshore Mall Lot",
    "NAVYPIER":    "Navy Pier",
    "RWALK":       "Road/Walk",
    "RINTER":      "Road Intersection",
    "FREEWAY":     "Freeway",
    "FWYLOD":      "Freeway LOD",
    "MANFACE":     "Man Face",
    "MALL":        "Mall",
    "PEDSTNSHW":   "Pedestrian Shadow",
    "BGSKY":       "Background Sky",
    "CARBOTTOM":   "Car Bottom",
    "CHECK":       "Checkpoint",
    "SHADMAP":     "Shadow Map",
    "SUITTIE":     "Suit & Tie",
    "TIRE":        "Tire Track",
    "TPSBUS":      "Bus (Traffic)",
    "TP":          "Traffic Prop",
    "PARTICLES":   "Particles",
    "EXPLOSION":   "Explosion",
    "PANOZ":       "Panoz (Car)",
}

# ── Suffix tokens ──────────────────────────────────────────────────────────────
SUFFIX_MAP = {
    "N":    "Night",
    "WIN":  "Winter",
    "FALL": "Fall",
    "NO":   "No Markings",
    "DMG":  "Damaged",
    "VL":   "Vending (Lit)",
    "BK":   "Back",
    "FT":   "Front",
    "SD":   "Side",
    "TP":   "Top",
    "BKLFT":"Back Left",
    "BKRGT":"Back Right",
    "SDLFT":"Side Left",
    "SDRGT":"Side Right",
    "TPBK": "Top Back",
    "TPFT": "Top Front",
    "SDFT": "Side Front",
    "SDBK": "Side Back",
    "DASH": "Dashboard",
    "DASHL":"Dashboard Left",
    "DASHM":"Dashboard Mid",
    "DASHR":"Dashboard Right",
    "WHL":  "Wheel",
    "WHLFT":"Wheel Front",
    "SHDW": "Shadow",
    "BD":   "Body",
    "SNEEDLE":"Speedometer Needle",
    "STRWHEEL":"Steering Wheel",
    "NEEDLE":  "Needle",
    "TOPLIGHT": "Top Light",
    "COPLIGHTS":"Cop Lights",
    "LIGHTSIGN":"Light Sign",
}

# ── Vehicle names ──────────────────────────────────────────────────────────────
VEHICLE_MAP = {
    "BUG":     "Beetle",
    "BULLET":  "Bullet GT",
    "BUS":     "Bus",
    "CADDIE":  "Cadillac",
    "COP":     "Police Car",
    "F350":    "Ford F-350",
    "FRD":     "Ford",
    "MUSTANG": "Mustang",
    "PANOZ":   "Panoz GTR-1",
}

# ── Season/time suffixes to strip and label ───────────────────────────────────
SEASON_SUFFIXES = {
    "WIN":  "Winter",
    "FALL": "Fall",
}
NIGHT_SUFFIX = "N"

# ── Variant numbers ───────────────────────────────────────────────────────────
def ordinal_suffix(n: int) -> str:
    return f" #{n}" if n > 0 else ""


def friendly_number(token: str) -> str:
    """Turn '01', '02', '2' etc. into ' #1', ' #2'."""
    try:
        return ordinal_suffix(int(token))
    except ValueError:
        return f" {token.title()}"


def make_friendly(name: str) -> str:
    """Convert a raw texture name to a human-readable label."""
    # ── Special-case full names ───────────────────────────────────────────────
    special = {
        "BGSKY":          "Background Sky",
        "CARBOTTOM":      "Car Bottom",
        "EXPLOSION":      "Explosion",
        "MANFACE":        "Man Face",
        "OPP_ICON":       "Opponent Icon",
        "PARTICLES":      "Particles",
        "PEDSTNSHW":      "Pedestrian Shadow",
        "ROAD":           "Road",
        "ROAD_N":         "Road (Night)",
        "RWALK":          "Roadside Walk",
        "RWALK_N":        "Roadside Walk (Night)",
        "RINTER":         "Road Intersection",
        "RINTER_N":       "Road Intersection (Night)",
        "SDWLK":          "Sidewalk",
        "SDWLK2":         "Sidewalk 2",
        "SDWLK_N":        "Sidewalk (Night)",
        "SNOW":           "Snow",
        "SNOW_N":         "Snow (Night)",
        "SUITTIE":        "Suit & Tie",
        "SUITTIE_N":      "Suit & Tie (Night)",
        "TIRE_TRACK":     "Tire Track",
        "TPSBUS":         "Traffic Bus",
        "MALL_SIGN":      "Mall Sign",
        "MALL_SIGN_N":    "Mall Sign (Night)",
        "LMMALL_LOT":     "Lakeshore Mall Lot",
        "LMMALL_LOT_N":   "Lakeshore Mall Lot (Night)",
        "CHECK_POINT_02": "Checkpoint #2",
        "CHECK04":        "Checkpoint #4",
        "FREEWAY2":       "Freeway 2",
        "FREEWAY2_N":     "Freeway 2 (Night)",
        "FREEWAY_EXITS":  "Freeway Exits",
        "FREEWAY_GRID":   "Freeway Grid",
        "FREEWAY_SIGN":   "Freeway Sign",
        "FWYLOD3":        "Freeway LOD 3",
        "FXLTCONE":       "FX Light Cone",
        "FXLTGLOW":       "FX Light Glow",
        "FXLTGLOWAMBER":  "FX Light Glow (Amber)",
        "FXLTGLOWRED":    "FX Light Glow (Red)",
        "RFWY":           "Ramp Freeway",
        "RFWY_N":         "Ramp Freeway (Night)",
        "RFWY_WIN":       "Ramp Freeway (Winter)",
        "RFWY_WIN_N":     "Ramp Freeway (Winter Night)",
        "RFWY_FALL":      "Ramp Freeway (Fall)",
        "RFWY_FALL_N":    "Ramp Freeway (Fall Night)",
        "IND_ROAD":       "Industrial Road",
        "IND_ASPHALT":    "Industrial Asphalt",
        "IND_ASPHALT_N":  "Industrial Asphalt (Night)",
        "IND_IBEAM":      "Industrial I-Beam",
        "IND_TIRE":       "Industrial Tire",
        "IND_SIDING_BOT": "Industrial Siding Bottom",
        "IND_SIDE_01":    "Industrial Side Panel",
        "IND_SIDE_01_N":  "Industrial Side Panel (Night)",
        "IND_TRUCK_SIDE": "Industrial Truck Side",
        "IND_TRUCK_SIDE_N":"Industrial Truck Side (Night)",
        "IND_TRUCK_UNDER":"Industrial Truck Underside",
        "IND_CLUB_SIGN":  "Industrial Club Sign",
        "IND_CLUB_SIGN_N":"Industrial Club Sign (Night)",
        "OT_PAWN":        "Old Town Pawn Shop",
        "OT_PHONESIDE":   "Old Town Phone Booth Side",
        "OT_PHONESIDE_N": "Old Town Phone Booth Side (Night)",
        "OT_PHONETOP":    "Old Town Phone Booth Top",
        "OT_PHONETOP_N":  "Old Town Phone Booth Top (Night)",
        "OT_LIGHT":       "Old Town Light",
        "OT_LIGHT_N":     "Old Town Light (Night)",
        "OT_RAIL":        "Old Town Rail",
        "OT_ROOF":        "Old Town Roof",
        "OT_ROOF_N":      "Old Town Roof (Night)",
        "OT_ROOFTRIM":    "Old Town Roof Trim",
        "OT_ROOFTRIM_N":  "Old Town Roof Trim (Night)",
        "DT_ROOF":        "Downtown Roof",
        "DT_ROOF_N":      "Downtown Roof (Night)",
        "H_ROOF":         "Hills Roof",
        "H_ROOF_N":       "Hills Roof (Night)",
        "IND_ROOF":       "Industrial Roof",
        "IND_ROOF_N":     "Industrial Roof (Night)",
        "IND_ROOF_01":    "Industrial Roof #1",
        "IND_ROOF_01_N":  "Industrial Roof #1 (Night)",
        "IND_WALL":       "Industrial Wall",
        "IND_WALL_N":     "Industrial Wall (Night)",
        "DT_UC_CRAN":     "Downtown Under Construction Crane",
        "DT_UC_DOOR":     "Downtown Under Construction Door",
        "DT_UC_STRCT":    "Downtown Under Construction Structure",
        "R_L_SIDE":       "Residential Landmark Side",
        "R_L_SIDE_N":     "Residential Landmark Side (Night)",
        "R_L_TRACK":      "Residential Landmark Track",
        "R_NAVYPIER":     "Navy Pier",
        "L_BOTTOM":       "Landmark Bottom",
        "L_BOTTOM_N":     "Landmark Bottom (Night)",
        "L_RIVET":        "Landmark Rivet",
        "L_RIVET_N":      "Landmark Rivet (Night)",
        "L_SIDE":         "Landmark Side",
        "L_SIDE_N":       "Landmark Side (Night)",
        "PANOZ_DASHL":    "Panoz GTR-1 Dashboard Left",
        "PANOZ_DASHM":    "Panoz GTR-1 Dashboard Mid",
        "PANOZ_DASHR":    "Panoz GTR-1 Dashboard Right",
        "PANOZ_SNEEDLE":  "Panoz GTR-1 Speedometer Needle",
        "PANOZ_STRWHEEL": "Panoz GTR-1 Steering Wheel",
        "VABUS_BK":       "Ambient Bus Back",
        "VABUS_FT":       "Ambient Bus Front",
        "VABUS_SD":       "Ambient Bus Side",
        "VABUS_TP":       "Ambient Bus Top",
        "VACOMP_WHL":     "Ambient Compact Wheel",
        "VAHEADLIGHT":    "Ambient Headlight",
        "VALIMO_WHL":     "Ambient Limo Wheel",
        "VASIGNALUNIT":   "Ambient Signal Unit",
        "VASTOPUNIT":     "Ambient Stop Unit",
        "VASWHL":         "Ambient Small Wheel",
        "VATAXI_BK":      "Ambient Taxi Back",
        "VATAXI_SD":      "Ambient Taxi Side",
        "VPFSHDW":        "Ford Shadow",
        "VPFWHL":         "Ford Wheel",
        "VPFRD_WHLFT":    "Ford Wheel Front",
        "VPF350_BD":      "Ford F-350 Body",
        "VPF350SHDW":     "Ford F-350 Shadow",
        "VPBUGSHDW":      "Beetle Shadow",
        "VPCOPLIGHTS":    "Police Car Lights",
        "VPCOP_TOPLIGHT": "Police Car Top Light",
    }
    if name in special:
        return special[name]

    parts = name.split("_")

    # ── Shadow map ─────────────────────────────────────────────────────────────
    if parts[0] == "SHADMAP":
        suffix_map = {
            "DAY":       "Day",
            "MORNEVE":   "Morning/Evening",
            "NITE":      "Night",
            "RAINSNOW":  "Rain/Snow",
        }
        label = suffix_map.get(parts[1], parts[1].title()) if len(parts) > 1 else ""
        return f"Shadow Map ({label})" if label else "Shadow Map"

    # ── Sky textures: SKY_DC, SKY_NF, etc. ────────────────────────────────────
    if parts[0] == "SKY" and len(parts) == 2 and len(parts[1]) == 2:
        time_map = {"D": "Day", "M": "Morning", "N": "Night", "S": "Sunset"}
        weather_map = {"C": "Clear", "F": "Fog", "R": "Rain", "S": "Snow"}
        t, w = parts[1][0], parts[1][1]
        time_label = time_map.get(t, t)
        weather_label = weather_map.get(w, w)
        return f"Sky ({time_label}, {weather_label})"

    if parts[0] == "SKY" and len(parts) == 3 and parts[2] == "FLASH":
        t, w = parts[1][0], parts[1][1]
        time_map = {"D": "Day", "M": "Morning", "N": "Night", "S": "Sunset"}
        weather_map = {"C": "Clear", "F": "Fog", "R": "Rain", "S": "Snow"}
        return f"Sky Lightning Flash ({time_map.get(t,t)}, {weather_map.get(w,w)})"

    # ── Reflection textures: REFL_DC etc. ─────────────────────────────────────
    if parts[0] == "REFL" and len(parts) == 2 and len(parts[1]) == 2:
        time_map = {"D": "Day", "M": "Morning", "N": "Night", "S": "Sunset"}
        weather_map = {"C": "Clear", "F": "Fog", "R": "Rain", "S": "Snow"}
        t, w = parts[1][0], parts[1][1]
        return f"Reflection ({time_map.get(t,t)}, {weather_map.get(w,w)})"

    # ── Numeric-prefix building textures: 01_DOOR, 07_BRICK_N, etc. ─────────
    if re.fullmatch(r"\d+", parts[0]):
        num = int(parts[0])
        qualifiers = []
        remaining = parts[1:]
        while remaining and remaining[-1] == NIGHT_SUFFIX:
            qualifiers.insert(0, "Night")
            remaining.pop()
        variant = ""
        if remaining and re.fullmatch(r"\d+", remaining[-1]) and len(remaining) > 1:
            variant = f" #{int(remaining[-1])}"
            remaining.pop()
        surface = " ".join(SURFACE_MAP.get(t, t.title()) for t in remaining)
        label = f"Building {num:02d} {surface}{variant}".strip()
        if qualifiers:
            label += f" ({', '.join(qualifiers)})"
        return label

    # ── Generic single-letter road/race markers: G_1..G_8, G_D, G_N, etc. ────
    if parts[0] == "G" and len(parts) == 2:
        label_map = {"D": "Day", "N": "Night", "P": "Pink", "R": "Red"}
        lbl = label_map.get(parts[1], f"#{parts[1]}")
        return f"Generic Marker {lbl}"

    # ── Race position markers: R1, R2, R4, R6 + season variants ──────────────
    if re.fullmatch(r"R\d+C?I?", parts[0]) and len(parts) <= 3:
        base = parts[0]
        road_labels = {
            "R1":   "Road 1",   "R2":   "Road 2",   "R4":   "Road 4",
            "R6":   "Road 6",   "R2C":  "Road 2C",  "R2I":  "Road 2I",
        }
        base_label = road_labels.get(base, base)
        qualifiers = []
        for p in parts[1:]:
            if p == "N":   qualifiers.append("Night")
            elif p == "WIN": qualifiers.append("Winter")
            elif p == "FALL": qualifiers.append("Fall")
            elif p == "NO": qualifiers.append("No Markings")
            else: qualifiers.append(p.title())
        qual_str = " ".join(qualifiers)
        return f"{base_label} {qual_str}".strip() if qual_str else base_label

    # ── Mall textures: MALL1..MALL5 ───────────────────────────────────────────
    if re.fullmatch(r"MALL\d+", name):
        return f"Mall {name[-1]}"

    # ── Particle effects: FXPT1..FXPT11, with _FALL/_WIN ─────────────────────
    if parts[0].startswith("FXPT"):
        num = parts[0][4:]
        qualifiers = []
        for p in parts[1:]:
            if p == "FALL":  qualifiers.append("Fall")
            elif p == "WIN": qualifiers.append("Winter")
            else: qualifiers.append(p.title())
        qual_str = " ".join(qualifiers)
        return f"Particle Effect {num} {qual_str}".strip() if qual_str else f"Particle Effect {num}"

    # ── Traffic prop lights ────────────────────────────────────────────────────
    if parts[0] == "TP" and len(parts) >= 2:
        rest = " ".join(p.title() for p in parts[1:])
        return f"Traffic Prop {rest}"

    # ── Vehicle parts (VP prefix) ─────────────────────────────────────────────
    # Names like VPBUGBLUE_BK have no underscore after VP, so parts[0] = "VPBUGBLUE"
    if parts[0].startswith("VP"):
        # Strip the leading VP and pass the rest as the first token
        first_no_vp = parts[0][2:]  # e.g. "BUGBLUE"
        return _friendly_vehicle([first_no_vp] + parts[1:])

    # ── Road textures T_GRASS_WIN_N pattern ───────────────────────────────────
    if parts[0] == "T" and len(parts) >= 2:
        return _friendly_T_prefix(parts[1:])

    # ── District-prefixed building textures ───────────────────────────────────
    district_codes = set(PREFIX_MAP.keys()) - {"VP", "VA", "FX", "SKY", "REFL", "FXPT", "T", "G", "L", "R"}
    if parts[0] in district_codes:
        return _friendly_district(parts[0], parts[1:])

    # ── Fallback: title-case with underscores replaced by spaces ──────────────
    return name.replace("_", " ").title()


def _friendly_vehicle(parts: list[str]) -> str:
    """Handle VP* vehicle texture names.

    The first token (parts[0]) is the combined {VEHICLENAME}{COLOR} string
    (e.g. BULLETBLUE, MUSTANGGREEN, CADDIERED).  Subsequent tokens (parts[1:])
    joined with _ form the part descriptor (e.g. BK_DMG, SD_VL, TPBK_DMG).
    """
    COLORS = {"BLUE","RED","WHITE","GREEN","GOLD","BLACK","ORANGE","YELLOW","GREY","GRAY"}
    COLOR_LABEL = {"GREY": "Gray"}

    first = parts[0]  # e.g. "BULLETBLUE" or "BULLET" or "COP"
    rest  = parts[1:] # e.g. ["BK","DMG"] or ["BKLFT"]

    # Try to peel a known color suffix off the first token
    vehicle_key = None
    color_label = None
    for color in sorted(COLORS, key=len, reverse=True):
        if first.endswith(color) and first != color:
            vehicle_candidate = first[: -len(color)]
            if vehicle_candidate in VEHICLE_MAP:
                vehicle_key = vehicle_candidate
                color_label = COLOR_LABEL.get(color, color.title())
                break

    if vehicle_key is None:
        # No color – whole first token is the vehicle key
        vehicle_key = first
        color_label = None

    vehicle_label = VEHICLE_MAP.get(vehicle_key, vehicle_key.title())

    # Decode part tokens
    part_str = "_".join(rest)
    part_tokens = []
    for tok in rest:
        if tok in SUFFIX_MAP:
            part_tokens.append(SUFFIX_MAP[tok])
        elif tok in SURFACE_MAP:
            part_tokens.append(SURFACE_MAP[tok])
        elif re.fullmatch(r"\d+", tok):
            part_tokens.append(f"#{tok}")
        else:
            part_tokens.append(tok.title())

    label = vehicle_label
    if color_label:
        label += f" ({color_label})"
    if part_tokens:
        label += " – " + " ".join(part_tokens)
    return label


def _resolve_surface(token: str) -> str:
    return SURFACE_MAP.get(token, token.replace("_", " ").title())


def _friendly_T_prefix(parts: list[str]) -> str:
    """Handle T_* texture names (town/terrain)."""
    if not parts:
        return "Town Texture"

    # Decode season/time qualifiers at the end
    qualifiers = []
    remaining = list(parts)

    # Strip trailing _N (night) and _WIN/_FALL (season) tokens
    while remaining:
        last = remaining[-1]
        if last == NIGHT_SUFFIX:
            qualifiers.insert(0, "Night")
            remaining.pop()
        elif last in SEASON_SUFFIXES:
            qualifiers.insert(0, SEASON_SUFFIXES[last])
            remaining.pop()
        else:
            break

    # Check for numbered variant at end (e.g. 01, 02)
    variant = ""
    if remaining and re.fullmatch(r"\d+", remaining[-1]):
        v = int(remaining[-1])
        variant = f" #{v}"
        remaining.pop()

    # The body tokens
    body = "_".join(remaining)

    # Known surface / terrain lookup
    known = SURFACE_MAP.get(body)
    if not known:
        # Try multi-word match
        known = SURFACE_MAP.get("_".join(remaining))
    if not known:
        known = body.replace("_", " ").title()

    label = f"Town {known}{variant}"
    if qualifiers:
        label += f" ({', '.join(qualifiers)})"
    return label


def _friendly_district(prefix: str, parts: list[str]) -> str:
    """Handle CT_*, DT_*, H_*, IND_*, OT_*, R_* patterns."""
    district = PREFIX_MAP.get(prefix, prefix.title())

    if not parts:
        return district

    # Decode season/night qualifiers from end
    qualifiers = []
    remaining = list(parts)

    while remaining:
        last = remaining[-1]
        if last == NIGHT_SUFFIX:
            qualifiers.insert(0, "Night")
            remaining.pop()
        elif last in SEASON_SUFFIXES:
            qualifiers.insert(0, SEASON_SUFFIXES[last])
            remaining.pop()
        else:
            break

    # Variant number at end
    variant = ""
    if remaining and re.fullmatch(r"\d+", remaining[-1]):
        v = int(remaining[-1])
        variant = f" #{v}"
        remaining.pop()

    if not remaining:
        qual_str = ", ".join(qualifiers)
        return f"{district}{variant} ({qual_str})" if qualifiers else f"{district}{variant}"

    first = remaining[0]

    # Try building type (e.g. APT2, BLDG01, HOTEL01, SHOP07 …)
    btype_match = re.fullmatch(r"([A-Z]+)(\d+)?", first)
    btype_key = btype_match.group(1) if btype_match else first
    btype_num  = int(btype_match.group(2)) if (btype_match and btype_match.group(2)) else None

    exact_match = BLDG_TYPE_MAP.get(first)
    if exact_match is not None:
        btype_label = exact_match
        btype_num_str = ""           # number already encoded in the label
    else:
        btype_label = BLDG_TYPE_MAP.get(btype_key, first.title())
        btype_num_str = f" {btype_num}" if btype_num else ""
    remaining = remaining[1:]

    # Surface token(s)
    surface_parts = []
    for tok in remaining:
        if re.fullmatch(r"\d+", tok):
            surface_parts.append(f"#{int(tok)}")
        elif tok in SURFACE_MAP:
            surface_parts.append(SURFACE_MAP[tok])
        else:
            surface_parts.append(tok.title())

    surface_str = " ".join(surface_parts)
    variant_str = variant

    label = f"{district} {btype_label}{btype_num_str}"
    if surface_str:
        label += f" {surface_str}{variant_str}"
    else:
        label += variant_str
    if qualifiers:
        label += f" ({', '.join(qualifiers)})"
    return label


def main():
    out_dir = Path(__file__).parent.parent / "tools"
    raw_out = out_dir / "texture_names.txt"
    friendly_out = out_dir / "texture_names_friendly.txt"

    files = sorted(
        f.stem for f in TEXTURE_DIR.iterdir()
        if f.is_file() and f.suffix.upper() == ".DDS"
    )

    with open(raw_out, "w", encoding="utf-8") as f:
        for name in files:
            f.write(name + "\n")

    with open(friendly_out, "w", encoding="utf-8") as f:
        f.write(f"{'Raw Name':<50} Friendly Name\n")
        f.write("-" * 90 + "\n")
        for name in files:
            friendly = make_friendly(name)
            f.write(f"{name:<50} {friendly}\n")

    print(f"Wrote {len(files)} textures to:")
    print(f"  {raw_out}")
    print(f"  {friendly_out}")


if __name__ == "__main__":
    main()
