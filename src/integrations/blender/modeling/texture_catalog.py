"""
Texture categorisation and friendly-name logic for the Blender UV panel.

Categories
----------
CURRENT   – only textures already used in the scene (always available)
BUILDINGS – district building textures (CT_/DT_/H_/IND_/OT_/R_/T_ prefixes and plain NN_ buildings)
ROADS     – road/pavement/terrain surfaces
VEHICLES  – VP* car textures, VA* ambient vehicles
EFFECTS   – FX*, SKY*, REFL*, SHADMAP, PARTICLES, EXPLOSION …
PROPS     – standalone props (signs, trees, fences, misc street furniture)
ALL       – every texture in the folder
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional


# ── Friendly-name helpers (same logic as tools/dump_texture_names.py) ─────────

_PREFIX_DISTRICT = {
    "CT": "Chinatown", "DT": "Downtown", "H": "Hills",
    "IND": "Industrial", "OT": "Old Town", "R": "Residential", "T": "Town",
}

_BLDG_TYPE = {
    "APT": "Apartment", "APT2": "Apartment 2", "APT3": "Apartment 3",
    "BNK": "Bank", "BLDG": "Building", "CLUB": "Club", "CONDO": "Condo",
    "DELI": "Deli", "DINR": "Diner", "FACT": "Factory", "FOOD": "Food Shop",
    "GUN": "Gun Shop", "HOME": "Home", "HOTEL": "Hotel",
    "HOUSE": "House", "HOUSE02": "House 2", "HOUSE03": "House 3",
    "INN": "Inn", "LIQR": "Liquor Store", "LIQUR": "Liquor Store",
    "MALL": "Mall", "MARKT": "Market", "MOTEL": "Motel",
    "OFFCE": "Office", "OFFICE": "Office", "PAWN": "Pawn Shop",
    "PIZZA": "Pizza Shop", "PIZA": "Pizza Shop", "PSTA": "Pasta Shop",
    "SCOTT": "Scott Building", "SHOP": "Shop", "SKY": "Skyscraper",
    "STOR": "Store", "THETR": "Theatre", "WOOD": "Wood Building",
    "BAR": "Bar", "UC": "Under Construction",
    "O": "Office", "B": "Blue Wing", "G": "Green Wing", "Y": "Yellow Brick",
}

_SURFACE = {
    "BRICK": "Brick", "BIRCK": "Brick", "WIN": "Window", "DOOR": "Door",
    "TRIM": "Trim", "WALL": "Wall", "ROOF": "Roof", "SIGN": "Sign",
    "SIDE": "Side", "AWNING": "Awning", "AWNING1": "Awning",
    "AWNING2": "Awning 2", "BANNER": "Banner", "BNR": "Banner",
    "CLOCK": "Clock", "CONCRETE": "Concrete", "CRETE": "Concrete",
    "ASPHALT": "Asphalt", "ASPHALTLINES": "Asphalt Lines",
    "GRASS": "Grass", "GRID": "Grid", "GRIDWORK": "Gridwork",
    "IBEAM": "I-Beam", "INDENT": "Indent", "INSIDE": "Inside",
    "LIGHT": "Light", "NEON": "Neon", "ONING": "Awning",
    "RAIL": "Rail", "RIVET": "Rivet", "ROAD": "Road",
    "ROCK": "Rock", "RUST": "Rust", "SIDING": "Siding",
    "SLIDINGDOOR": "Sliding Door", "STEP": "Step", "TARP": "Tarp",
    "TIN": "Tin", "TOP": "Top", "TRACK": "Track", "TUN": "Tunnel",
    "VENT": "Vent", "WATER": "Water", "WOOD": "Wood",
    "TREE": "Tree", "SNOW": "Snow", "DIRT": "Dirt", "GLASS": "Glass",
    "FLOOR": "Floor", "WALK": "Walkway", "ALLEY": "Alley",
    "TRASH": "Trash", "MAIL": "Mail Box", "POSTER": "Poster",
    "ATM": "ATM", "BOOTH": "Booth", "SCORBD": "Scoreboard",
    "STAT": "Statue", "DUCK": "Duck", "CRAN": "Crane",
    "STRCT": "Structure", "MEDIABOX": "Media Box", "RUBLE": "Rubble",
    "FIRE": "Fire", "SIGNPROP": "Sign Prop", "BARRICADE": "Barricade",
    "CAUTION": "Caution", "BOX": "Box", "METER": "Meter",
    "NEWS": "Newsstand", "PHONE": "Phone", "POLE": "Pole",
    "LIGHTARCH": "Light Arch",
}

_SUFFIX = {
    "N": "Night", "WIN": "Winter", "FALL": "Fall", "NO": "No Markings",
    "DMG": "Damaged", "VL": "Lit",
    "BK": "Back", "FT": "Front", "SD": "Side", "TP": "Top",
    "BKLFT": "Back Left", "BKRGT": "Back Right",
    "SDLFT": "Side Left", "SDRGT": "Side Right",
    "TPBK": "Top Back", "TPFT": "Top Front",
    "DASHL": "Dash Left", "DASHM": "Dash Mid", "DASHR": "Dash Right",
    "WHL": "Wheel", "WHLFT": "Wheel Front", "SHDW": "Shadow", "BD": "Body",
    "SNEEDLE": "Speedo Needle", "STRWHEEL": "Steering Wheel",
    "TOPLIGHT": "Top Light", "COPLIGHTS": "Cop Lights",
}

_VEHICLE = {
    "BUG": "Beetle", "BULLET": "Bullet GT", "BUS": "Bus",
    "CADDIE": "Cadillac", "COP": "Police Car",
    "F350": "Ford F-350", "FRD": "Ford", "MUSTANG": "Mustang",
}

_COLORS = {"BLUE", "RED", "WHITE", "GREEN", "GOLD", "BLACK", "ORANGE", "YELLOW", "GREY", "GRAY"}
_COLOR_LABEL = {"GREY": "Gray"}

_SEASON = {"WIN": "Winter", "FALL": "Fall"}
_NIGHT  = "N"

_TIME_MAP    = {"D": "Day", "M": "Morning", "N": "Night", "S": "Sunset"}
_WEATHER_MAP = {"C": "Clear", "F": "Fog", "R": "Rain", "S": "Snow"}


def _ordinal(tok: str) -> str:
    try:
        return f"#{int(tok)}"
    except ValueError:
        return tok.title()


def _strip_season_night(parts: list[str]) -> tuple[list[str], list[str]]:
    qualifiers: list[str] = []
    remaining = list(parts)
    while remaining:
        last = remaining[-1]
        if last == _NIGHT:
            qualifiers.insert(0, "Night")
            remaining.pop()
        elif last in _SEASON:
            qualifiers.insert(0, _SEASON[last])
            remaining.pop()
        else:
            break
    return remaining, qualifiers


def _strip_variant(parts: list[str]) -> tuple[list[str], str]:
    if parts and re.fullmatch(r"\d+", parts[-1]):
        return parts[:-1], f" #{int(parts[-1])}"
    return parts, ""


def _friendly_vehicle(first_no_vp: str, rest: list[str]) -> str:
    color_label: Optional[str] = None
    vehicle_key = first_no_vp
    for color in sorted(_COLORS, key=len, reverse=True):
        if first_no_vp.endswith(color) and first_no_vp != color:
            candidate = first_no_vp[: -len(color)]
            if candidate in _VEHICLE:
                vehicle_key = candidate
                color_label = _COLOR_LABEL.get(color, color.title())
                break

    vehicle_label = _VEHICLE.get(vehicle_key, vehicle_key.title())
    part_tokens = [_SUFFIX.get(t, _SURFACE.get(t, t.title())) for t in rest]

    label = vehicle_label
    if color_label:
        label += f" ({color_label})"
    if part_tokens:
        label += " – " + " ".join(part_tokens)
    return label


def _friendly_district(prefix: str, parts: list[str]) -> str:
    district = _PREFIX_DISTRICT.get(prefix, prefix.title())
    if not parts:
        return district

    remaining, qualifiers = _strip_season_night(parts)
    remaining, variant = _strip_variant(remaining if (remaining and re.fullmatch(r"\d+", remaining[-1]) and len(remaining) > 1) else remaining)

    if not remaining:
        label = district + variant
        return f"{label} ({', '.join(qualifiers)})" if qualifiers else label

    first = remaining[0]
    btype_match = re.fullmatch(r"([A-Z]+)(\d+)?", first)
    btype_key   = btype_match.group(1) if btype_match else first
    btype_num   = int(btype_match.group(2)) if (btype_match and btype_match.group(2)) else None

    exact = _BLDG_TYPE.get(first)
    if exact is not None:
        btype_label   = exact
        btype_num_str = ""
    else:
        btype_label   = _BLDG_TYPE.get(btype_key, first.title())
        btype_num_str = f" {btype_num}" if btype_num else ""

    surface_parts = []
    for tok in remaining[1:]:
        if re.fullmatch(r"\d+", tok):
            surface_parts.append(f"#{int(tok)}")
        else:
            surface_parts.append(_SURFACE.get(tok, tok.title()))

    label = f"{district} {btype_label}{btype_num_str}"
    if surface_parts:
        label += f" {' '.join(surface_parts)}{variant}"
    else:
        label += variant
    return f"{label} ({', '.join(qualifiers)})" if qualifiers else label


_PLAIN_NAMES: dict[str, str] = {
    "ROAD": "Road", "ROAD_N": "Road (Night)",
    "RFWY": "Ramp Freeway", "RFWY_N": "Ramp Freeway (Night)",
    "RFWY_WIN": "Ramp Freeway (Winter)", "RFWY_WIN_N": "Ramp Freeway (Winter, Night)",
    "RFWY_FALL": "Ramp Freeway (Fall)", "RFWY_FALL_N": "Ramp Freeway (Fall, Night)",
    "RWALK": "Roadside Walk", "RWALK_N": "Roadside Walk (Night)",
    "RINTER": "Road Intersection", "RINTER_N": "Road Intersection (Night)",
    "SDWLK": "Sidewalk", "SDWLK2": "Sidewalk 2", "SDWLK_N": "Sidewalk (Night)",
    "FREEWAY2": "Freeway 2", "FREEWAY2_N": "Freeway 2 (Night)",
    "FREEWAY_EXITS": "Freeway Exits", "FREEWAY_GRID": "Freeway Grid",
    "FREEWAY_SIGN": "Freeway Sign", "FWYLOD3": "Freeway LOD 3",
    "SNOW": "Snow", "SNOW_N": "Snow (Night)",
    "BGSKY": "Background Sky", "CARBOTTOM": "Car Bottom",
    "EXPLOSION": "Explosion", "PARTICLES": "Particles",
    "PEDSTNSHW": "Pedestrian Shadow", "MANFACE": "Man Face",
    "SUITTIE": "Suit & Tie", "SUITTIE_N": "Suit & Tie (Night)",
    "TIRE_TRACK": "Tire Track", "OPP_ICON": "Opponent Icon",
    "MALL_SIGN": "Mall Sign", "MALL_SIGN_N": "Mall Sign (Night)",
    "LMMALL_LOT": "Lakeshore Mall Lot", "LMMALL_LOT_N": "Lakeshore Mall Lot (Night)",
    "CHECK_POINT_02": "Checkpoint 2", "CHECK04": "Checkpoint 4",
    "IND_ROAD": "Industrial Road",
    "IND_ASPHALT": "Industrial Asphalt", "IND_ASPHALT_N": "Industrial Asphalt (Night)",
    "IND_IBEAM": "Industrial I-Beam", "IND_TIRE": "Industrial Tire",
    "IND_SIDING_BOT": "Industrial Siding Bottom",
    "IND_TRUCK_SIDE": "Industrial Truck Side",
    "IND_TRUCK_SIDE_N": "Industrial Truck Side (Night)",
    "IND_TRUCK_UNDER": "Industrial Truck Underside",
    "FXLTCONE": "FX Light Cone", "FXLTGLOW": "FX Light Glow",
    "FXLTGLOWAMBER": "FX Light Glow (Amber)", "FXLTGLOWRED": "FX Light Glow (Red)",
    "FXPARTICLE02": "FX Particle 02",
    "PANOZ_DASHL": "Panoz GTR-1 – Dash Left", "PANOZ_DASHM": "Panoz GTR-1 – Dash Mid",
    "PANOZ_DASHR": "Panoz GTR-1 – Dash Right",
    "PANOZ_SNEEDLE": "Panoz GTR-1 – Speedo Needle",
    "PANOZ_STRWHEEL": "Panoz GTR-1 – Steering Wheel",
    "VABUS_BK": "Ambient Bus – Back", "VABUS_FT": "Ambient Bus – Front",
    "VABUS_SD": "Ambient Bus – Side", "VABUS_TP": "Ambient Bus – Top",
    "VACOMP_WHL": "Ambient Compact – Wheel",
    "VAHEADLIGHT": "Ambient Headlight", "VALIMO_WHL": "Ambient Limo – Wheel",
    "VASIGNALUNIT": "Ambient Signal Unit", "VASTOPUNIT": "Ambient Stop Unit",
    "VASWHL": "Ambient Small Wheel", "VATAXI_BK": "Ambient Taxi – Back",
    "VATAXI_SD": "Ambient Taxi – Side",
    "VPFSHDW": "Ford – Shadow", "VPFWHL": "Ford – Wheel",
    "VPFRD_WHLFT": "Ford – Front Wheel", "VPF350_BD": "Ford F-350 – Body",
    "VPF350SHDW": "Ford F-350 – Shadow", "VPBUGSHDW": "Beetle – Shadow",
    "VPCOPLIGHTS": "Police Car – Lights", "VPCOP_TOPLIGHT": "Police Car – Top Light",
    "MALL1": "Mall Texture 1", "MALL2": "Mall Texture 2", "MALL3": "Mall Texture 3",
    "MALL4": "Mall Texture 4", "MALL5": "Mall Texture 5",
    "R_NAVYPIER": "Navy Pier", "R_L_SIDE": "Landmark Side",
    "R_L_SIDE_N": "Landmark Side (Night)", "R_L_TRACK": "Landmark Track",
    "L_BOTTOM": "Landmark Bottom", "L_BOTTOM_N": "Landmark Bottom (Night)",
    "L_RIVET": "Landmark Rivet (Ice)", "L_RIVET_N": "Landmark Rivet (Night)",
    "L_SIDE": "Landmark Side", "L_SIDE_N": "Landmark Side (Night)",
    "DT_ROOF": "Downtown Roof", "DT_ROOF_N": "Downtown Roof (Night)",
    "H_ROOF": "Hills Roof", "H_ROOF_N": "Hills Roof (Night)",
    "IND_ROOF": "Industrial Roof", "IND_ROOF_N": "Industrial Roof (Night)",
    "IND_ROOF_01": "Industrial Roof #1", "IND_ROOF_01_N": "Industrial Roof #1 (Night)",
    "IND_WALL": "Industrial Wall", "IND_WALL_N": "Industrial Wall (Night)",
    "OT_RAIL": "Old Town Rail", "OT_ROOF": "Old Town Roof",
    "OT_ROOF_N": "Old Town Roof (Night)",
    "OT_ROOFTRIM": "Old Town Roof Trim", "OT_ROOFTRIM_N": "Old Town Roof Trim (Night)",
    "OT_LIGHT": "Old Town Light", "OT_LIGHT_N": "Old Town Light (Night)",
    "OT_PAWN": "Old Town Pawn Shop",
    "OT_PHONESIDE": "Old Town Phone Booth Side",
    "OT_PHONESIDE_N": "Old Town Phone Booth Side (Night)",
    "OT_PHONETOP": "Old Town Phone Booth Top",
    "OT_PHONETOP_N": "Old Town Phone Booth Top (Night)",
    "OT_STAT": "Old Town Statue", "OT_STAT_N": "Old Town Statue (Night)",
    "OT_SCORBD": "Old Town Scoreboard", "OT_SCORBD_N": "Old Town Scoreboard (Night)",
    "DT_UC_CRAN": "Downtown UC Crane", "DT_UC_DOOR": "Downtown UC Door",
    "DT_UC_STRCT": "Downtown UC Structure",
    "TP_LIGHT": "Traffic Prop Light", "TP_LIGHT_N": "Traffic Prop Light (Night)",
    "TPSBUS": "Traffic Bus", "SHADMAP_DAY": "Shadow Map (Day)",
    "SHADMAP_MORNEVE": "Shadow Map (Morning/Evening)",
    "SHADMAP_NITE": "Shadow Map (Night)", "SHADMAP_RAINSNOW": "Shadow Map (Rain/Snow)",
    "IND_CLUB_SIGN": "Industrial Club Sign",
    "IND_CLUB_SIGN_N": "Industrial Club Sign (Night)",
    "IND_SIDE_01": "Industrial Side Panel", "IND_SIDE_01_N": "Industrial Side Panel (Night)",
}


def make_friendly(name: str) -> str:
    """Convert a raw DDS stem (no extension) to a human-readable label."""
    # ── Exact-match table first ────────────────────────────────────────────────
    if name in _PLAIN_NAMES:
        return _PLAIN_NAMES[name]

    parts = name.split("_")

    # ── Numeric building prefix: 01_WIN_N ─────────────────────────────────────
    # NB: for numeric prefix, WIN means Window (surface), not Winter (season),
    #     so we DO NOT call _strip_season_night. Parse directly.
    if re.fullmatch(r"\d+", parts[0]):
        num = int(parts[0])
        rest = parts[1:]
        # Strip only pure night suffix _N at the very end; WIN here = Window not Winter
        night = ""
        if rest and rest[-1] == "N":
            night = " (Night)"
            rest = rest[:-1]
        # Strip variant number (e.g. _02, _03)
        variant = ""
        if len(rest) > 1 and re.fullmatch(r"\d+", rest[-1]):
            variant = f" #{int(rest[-1])}"
            rest = rest[:-1]
        surface = " ".join(_SURFACE.get(t, t.title()) for t in rest)
        return f"Building {num:02d} {surface}{variant}{night}".strip()

    # ── Sky / Reflection 2-char codes: SKY_DC, REFL_NR ───────────────────────
    if parts[0] in ("SKY", "REFL") and len(parts) == 2 and len(parts[1]) == 2:
        t, w = parts[1][0], parts[1][1]
        tl   = _TIME_MAP.get(t, t)
        wl   = _WEATHER_MAP.get(w, w)
        prefix = "Sky" if parts[0] == "SKY" else "Reflection"
        return f"{prefix} ({tl}, {wl})"

    if parts[0] == "SKY" and len(parts) == 3 and parts[2] == "FLASH":
        t, w = parts[1][0], parts[1][1]
        return f"Sky Lightning ({_TIME_MAP.get(t,t)}, {_WEATHER_MAP.get(w,w)})"

    # ── Shadow map ─────────────────────────────────────────────────────────────
    if parts[0] == "SHADMAP":
        lbl = {"DAY": "Day", "MORNEVE": "Morning/Evening", "NITE": "Night", "RAINSNOW": "Rain/Snow"}.get(parts[1] if len(parts) > 1 else "", "")
        return f"Shadow Map ({lbl})" if lbl else "Shadow Map"

    # ── Generic markers: G_1, G_N ─────────────────────────────────────────────
    if parts[0] == "G" and len(parts) == 2:
        lbl = {"D": "Day", "N": "Night", "P": "Pink", "R": "Red"}.get(parts[1], f"#{parts[1]}")
        return f"Generic Marker {lbl}"

    # ── Road surfaces R1, R2C, R2I … ─────────────────────────────────────────
    if re.fullmatch(r"R\d+[CI]?", parts[0]) and len(parts) <= 3:
        road_labels = {
            "R1": "Road 1", "R2": "Road 2", "R4": "Road 4", "R6": "Road 6",
            "R2C": "Road 2C", "R2I": "Road 2I",
        }
        base  = road_labels.get(parts[0], parts[0])
        quals = []
        for p in parts[1:]:
            quals.append({"N": "Night", "WIN": "Winter", "FALL": "Fall", "NO": "No Markings"}.get(p, p.title()))
        return (base + " " + " ".join(quals)).strip()

    # ── Particle effects: FXPT5_WIN ───────────────────────────────────────────
    if parts[0].startswith("FXPT"):
        num  = parts[0][4:]
        qual = " ".join({"FALL": "Fall", "WIN": "Winter"}.get(p, p.title()) for p in parts[1:])
        return f"Particle {num} {qual}".strip() if qual else f"Particle {num}"

    # ── Ramp/freeway: RFWY + season/night ─────────────────────────────────────
    if parts[0] == "RFWY":
        remaining, qualifiers = _strip_season_night(parts[1:])
        label = "Ramp Freeway"
        return f"{label} ({', '.join(qualifiers)})" if qualifiers else label

    # ── Vehicle parts VP* ─────────────────────────────────────────────────────
    if parts[0].startswith("VP"):
        return _friendly_vehicle(parts[0][2:], parts[1:])

    # ── District building textures ─────────────────────────────────────────────
    if parts[0] in _PREFIX_DISTRICT:
        return _friendly_district(parts[0], parts[1:])

    # ── Town textures T_* ─────────────────────────────────────────────────────
    if parts[0] == "T" and len(parts) >= 2:
        remaining, qualifiers = _strip_season_night(parts[1:])
        remaining, variant    = _strip_variant(remaining if len(remaining) > 1 else remaining)
        body = "_".join(remaining)
        known = _SURFACE.get(body) or _SURFACE.get(remaining[0] if remaining else "")
        label = f"Town {known or body.replace('_',' ').title()}{variant}"
        return f"{label} ({', '.join(qualifiers)})" if qualifiers else label

    # ── Fallback ───────────────────────────────────────────────────────────────
    return name.replace("_", " ").title()


# ── Category definitions ───────────────────────────────────────────────────────

CATEGORY_ITEMS = [
    ("CURRENT",     "Current",        "Only textures already used in the scene"),
    ("RECOMMENDED", "Recommended",    "Curated list — edit src/USER/settings/recommended_textures.py"),
    ("BUILDINGS",   "Buildings",      "District building textures (facades, doors, windows, bricks …)"),
    ("ROADS",       "Roads & Terrain","Road surfaces, pavement, grass, water, snow …"),
    ("VEHICLES",    "Vehicles",       "Car and bus textures (VP* / VA*)"),
    ("EFFECTS",     "Effects & Sky",  "Sky, reflections, particles, explosions, shadow maps …"),
    ("PROPS",     "Props & Signs",  "Street furniture, signs, trees, barriers …"),
    ("ALL",       "All Textures",   "Every texture in the folder (1800+ entries — slow!)"),
]

# Prefix / pattern sets per category
_BUILDING_PREFIXES = {"CT", "DT", "H", "IND", "OT", "R", "T"}

def _is_building(stem: str) -> bool:
    parts = stem.split("_")
    if re.fullmatch(r"\d+", parts[0]):
        return True
    p0 = parts[0]
    if p0 in _BUILDING_PREFIXES and len(parts) > 1:
        # Exclude road/terrain T_ entries (handled in ROADS)
        if p0 == "T":
            return False
        # Exclude R_ road surfaces
        if p0 == "R" and re.fullmatch(r"R\d+[CI]?", stem.split("_")[0]):
            return False
        return True
    return False

def _is_road(stem: str) -> bool:
    parts = stem.split("_")
    # R1/R2/R4/R6 road surfaces
    if re.fullmatch(r"R\d+[CI]?", parts[0]):
        return True
    # T_ terrain
    if parts[0] == "T":
        terrain_keys = {
            "GRASS", "WATER", "SNOW", "DIRT", "ASPHALT", "ASPHALTLINES",
            "CONCRETE", "CONCRETE01", "WALL", "WALL02", "WALK", "ALLEY",
            "JERSEY", "RAIL", "RAIL03", "RAIL_01", "GRID",
        }
        return parts[1] if len(parts) > 1 and parts[1] in terrain_keys else False
    # Explicit road names
    plain_roads = {
        "ROAD", "RFWY", "RWALK", "RINTER", "SDWLK", "SDWLK2",
        "IND_ROAD", "IND_ASPHALT", "FREEWAY2", "FREEWAY_EXITS",
        "FREEWAY_GRID", "FREEWAY_SIGN", "FWYLOD3",
        "T_ASPHALT", "T_ASPHALTLINES", "T_CONCRETE01", "T_CONCRETE_NO",
        "T_DIRT", "T_GRASS", "T_WATER", "T_WALL", "T_WALL02",
        "T_WALK_ALLEY", "T_RAIL", "T_RAIL_01", "T_RAIL03",
        "T_JERSEY_RAIL", "T_GRID",
        "SNOW",
    }
    for road in plain_roads:
        if stem == road or stem.startswith(road + "_"):
            return True
    return False

def _is_vehicle(stem: str) -> bool:
    return stem.startswith("VP") or stem.startswith("VA") or stem.startswith("PANOZ")

def _is_effect(stem: str) -> bool:
    effects = ("SKY_", "REFL_", "SHADMAP_", "FXPT", "FXLT", "FX", "BGSKY",
               "RFWY", "EXPLOSION", "PARTICLES", "PEDSTNSHW", "MALL1", "MALL2",
               "MALL3", "MALL4", "MALL5")
    if any(stem.startswith(e) for e in effects):
        return True
    if re.fullmatch(r"SKY_\w+", stem) or re.fullmatch(r"REFL_\w+", stem):
        return True
    return False

def _is_prop(stem: str) -> bool:
    prop_patterns = (
        "T_TREE", "T_STOP", "T_SIGN", "T_POLE", "T_PHONE", "T_METER",
        "T_MAIL", "T_NEWS", "T_BARRICADE", "T_CAUTION", "T_BOX",
        "T_USFLAG", "T_LIGHT", "T_STEP", "T_SLIDINGDOOR", "T_DMPSTRFRNT",
        "T_DO_NOT_ENTER", "T_WRONGWAY", "T_1WAY", "T_2WAY", "T_75",
        "T_L_ONLY", "T_NO_PARK", "T_RED_BLACK",
        "T_SHIP", "T_FISH", "T_CARDBORDBOX", "T_RUBLE", "T_TRASH",
        "T_CD_SIGN", "T_DEPT_SIGN", "T_DRUG_SIGN", "T_CLUB_SIGN",
        "T_EXIT", "T_TUN", "T_BLACK",
        "OT_LIGHTSIGN", "OT_LIGHT", "OT_STAT", "OT_PAWN",
        "OT_PHONESIDE", "OT_PHONETOP", "OT_RAIL", "OT_SCORBD",
        "CT_DUCK", "CT_FIRE", "CT_NEON", "CT_AWNING", "CT_BANNER",
        "IND_TIRE", "IND_IBEAM", "IND_TRUCK", "IND_VENT",
        "IND_SIGN", "IND_RUST", "IND_SLIDINGDOOR",
        "FXLTCONE", "FXLTGLOW", "TP_LIGHT", "TPSBUS",
        "CHECK", "OPP_ICON", "MANFACE", "SUITTIE",
        "TIRE_TRACK", "CARBOTTOM", "FREEWAY_SIGN",
        "MALL_SIGN", "LMMALL_LOT",
    )
    return any(stem.startswith(p) or stem == p for p in prop_patterns)


def categorise(stem: str) -> str:
    """Return the category key for a texture stem."""
    if _is_vehicle(stem):  return "VEHICLES"
    if _is_effect(stem):   return "EFFECTS"
    if _is_road(stem):     return "ROADS"
    if _is_prop(stem):     return "PROPS"
    if _is_building(stem): return "BUILDINGS"
    return "PROPS"   # catch-all for misc items


def build_recommended(texture_folder: Path) -> list[tuple[str, str, str]]:
    """Build the Recommended list from src/USER/settings/recommended_textures.py.

    Order follows the declaration in that file exactly. Only entries whose DDS
    file actually exists in *texture_folder* are included.
    """
    try:
        from src.USER.settings.recommended_textures import RECOMMENDED_TEXTURES
    except ImportError:
        return []

    seen: set[str] = set()
    items: list[tuple[str, str, str]] = []
    for raw in RECOMMENDED_TEXTURES:
        stem = raw.upper().replace(".DDS", "").replace(".dds", "")
        if stem in seen:
            continue
        seen.add(stem)
        dds_path = texture_folder / f"{stem}.DDS"
        if not dds_path.exists():
            continue
        items.append((stem, make_friendly(stem), stem))
    return items


def build_catalog(texture_folder: Path) -> dict[str, list[tuple[str, str, str]]]:
    """
    Scan *texture_folder* and return a dict mapping category key → sorted list
    of (identifier, label, description) enum tuples.
    """
    catalog: dict[str, list] = {key: [] for key, *_ in CATEGORY_ITEMS if key not in ("CURRENT", "ALL", "RECOMMENDED")}

    for dds in sorted(texture_folder.glob("*.DDS")):
        stem  = dds.stem
        label = make_friendly(stem)
        item  = (stem, label, stem)
        cat   = categorise(stem)
        catalog[cat].append(item)

    for cat in catalog:
        catalog[cat].sort(key=lambda x: x[1])

    catalog["RECOMMENDED"] = build_recommended(texture_folder)

    return catalog
