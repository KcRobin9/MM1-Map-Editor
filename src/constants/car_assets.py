"""
Car asset catalogues — friendly names for textures, sounds, etc.

Used by the Blender Car Editor to populate dropdowns with human-readable
labels instead of raw game filenames.
"""


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
