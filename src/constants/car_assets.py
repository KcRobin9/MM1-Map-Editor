"""
Car asset catalogues — friendly names for textures, sounds, etc.

Used by the Blender Car Editor to populate dropdowns with human-readable
labels instead of raw game filenames.
"""


class Vehicle:
    """
    Friendly names for car folders (resources/editor/MESHES/CARS/*).

    Player cars (VP*) are listed first so dropdowns default to a sensible car
    (Mustang) rather than an ambient/odd entry. Ambient cars (VA*) follow.
    """
    CATALOGUE = [
        ("VPMUSTANG99", "Ford Mustang"),
        ("VPPANOZ",     "Panoz Roadster"),
        ("VPPANOZGT",   "Panoz GTR-1"),
        ("VPCADDIE",    "Cadillac"),
        ("VPBUG",       "Beetle"),
        ("VPBULLET",    "Bullet"),
        ("VPFORD",      "Ford F-350"),
        ("VPCOP",       "Police Car"),
        ("VPBUS",       "Bus"),
        ("VPSEMI",      "Semi"),
        ("VACOMPACT",   "Compact (ambient)"),
        ("VASEDANS",    "Sedan (ambient)"),
        ("VASEDANL",    "Sedan L (ambient)"),
        ("VALIMO",      "Limo (ambient)"),
        ("VAPICKUP",    "Pickup (ambient)"),
        ("VAVAN",       "Van (ambient)"),
        ("VATAXI",      "Taxi (ambient)"),
        ("VADELIVERY",  "Delivery (ambient)"),
        ("VADIESELS",   "Diesel (ambient)"),
        ("VABUS",       "City Bus (ambient)"),
        ("VABOEING_SMALL", "Plane (ambient)"),
    ]

    LABELS = {stem: label for stem, label in CATALOGUE}
    ORDER  = {stem: i for i, (stem, _) in enumerate(CATALOGUE)}

    @classmethod
    def label(cls, folder_name: str) -> str:
        return cls.LABELS.get(
            folder_name.upper(),
            folder_name.replace("VP", "", 1).replace("VA", "", 1).title() or folder_name,
        )


class WheelTexture:
    """
    Known wheel textures from resources/editor/TEXTURES/.
    Each entry: (texture_stem, friendly_label)
    """
    CATALOGUE = [
        ("VPCOP_WHL",      "Police / Mustang"),
        ("VPBUG_WHL",      "Bug"),
        ("VPCAD_WHL",      "Cadillac"),
        ("VPFWHL",         "Ford Mustang"),
        ("VPFRD_WHLFT",    "Ford F-350"),
        ("VPPANOZGTWHL",   "Panoz GTR-1"),
        ("VPSEMI_WHLFT",   "Semi"),
        ("VACOMP_WHL",     "Compact"),
        ("VALIMO_WHL",     "Limo"),
        ("VASWHL",         "Sedan"),
    ]

    # Quick lookup: stem → label
    LABELS = {stem: label for stem, label in CATALOGUE}

    @classmethod
    def blender_items(cls, tex_folder):
        """
        Return an EnumProperty items list for all WHL textures found in
        tex_folder, using friendly labels where known and falling back to
        the raw stem otherwise.  Files are ordered by CATALOGUE first,
        then any unlisted extras alphabetically.
        """
        try:
            on_disk = {
                f.stem.upper(): f.stem
                for f in tex_folder.iterdir()
                if f.suffix.upper() == ".DDS" and "WHL" in f.stem.upper()
            }
        except OSError:
            on_disk = {}

        seen  = set()
        items = []

        # Catalogue order first
        for stem, label in cls.CATALOGUE:
            key = stem.upper()
            if key in on_disk:
                items.append((on_disk[key], label, ""))
                seen.add(key)

        # Any extras on disk not in the catalogue
        for key in sorted(on_disk):
            if key not in seen:
                items.append((on_disk[key], on_disk[key], ""))

        return items or [("VPCOP_WHL", "Police / Mustang", "")]


class LightColor:
    """
    Glow colours for car / siren light meshes (head, tail, brake, signals, siren).

    Each entry maps a colour SUFFIX — appended to a white base texture stem
    (FXLTGLOW for glows, FXLTCONE for the headlight beam) — to its friendly label
    and an (R, G, B) tint. White / Red / Amber ship with the game; the rest are
    generated on demand by tinting the white source DDS (see the Car Editor's
    _tint_dds_a4r4g4b4).

        (suffix, label, description, (r, g, b))
    """
    CATALOGUE = [
        ("",       "White",  "Plain white glow (headlights, reverse)",              (1.0, 1.0, 1.0)),
        ("RED",    "Red",    "Red glow (tail / brake lights)",                      (1.0, 0.05, 0.05)),
        ("AMBER",  "Amber",  "Amber glow (turn signals)",                           (1.0, 0.55, 0.05)),
        ("BLUE",   "Blue",   "Blue glow (police) — generated; best on custom cars", (0.10, 0.25, 1.0)),
        ("GREEN",  "Green",  "Green glow — generated; best on custom cars",          (0.10, 1.0, 0.25)),
        ("PURPLE", "Purple", "Purple glow — generated; best on custom cars",         (0.65, 0.10, 1.0)),
        ("CYAN",   "Cyan",   "Cyan glow — generated; best on custom cars",           (0.10, 0.95, 1.0)),
        ("PINK",   "Pink",   "Pink glow — generated; best on custom cars",           (1.0, 0.20, 0.70)),
        ("ORANGE", "Orange", "Orange glow — generated; best on custom cars",         (1.0, 0.35, 0.0)),
        ("LIME",   "Lime",   "Lime glow — generated; best on custom cars",           (0.65, 1.0, 0.10)),
    ]

    # Stock light textures shipped in the game's GLOBAL.TSH — they resolve globally
    # and are never packed. Any other FXLT* texture (a generated colour) must be
    # packed into the car's TEX16A and declared in its TSH.
    GLOBAL_TEXTURES = {"FXLTGLOW", "FXLTGLOWRED", "FXLTGLOWAMBER", "FXLTCONE"}

    # suffix → (r, g, b)
    SUFFIX_RGB = {suffix: rgb for suffix, _label, _desc, rgb in CATALOGUE}

    # Every glow texture name: white base + each coloured variant.
    TEXTURES = [f"FXLTGLOW{suffix}" for suffix, _l, _d, _rgb in CATALOGUE]

    @classmethod
    def blender_items(cls):
        """EnumProperty items list: (FXLTGLOW{suffix}, label, description)."""
        return [(f"FXLTGLOW{suffix}", label, desc)
                for suffix, label, desc, _rgb in cls.CATALOGUE]
