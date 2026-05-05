import bpy
import math

from src.constants.textures import Texture

from pathlib import Path
from src.constants.file_formats import FileType

from src.integrations.blender.modeling.texture_catalog import (
    build_catalog, make_friendly, categorise, CATEGORY_ITEMS,
)


_texture_folder: Path | None = None

# Full per-category catalog (populated once the texture folder is known).
# Key → sorted list of (id, label, tooltip) enum tuples.
_catalog: dict[str, list] = {}

# Which categories have already had their DDS files loaded into bpy.data.images.
_loaded_categories: set[str] = set()

# Stable cached list for the CURRENT category.
# Rebuilt only by refresh_current_textures() — never on every draw call.
_current_items: list[tuple] = []


def set_texture_folder(folder) -> None:
    global _texture_folder, _catalog, _loaded_categories
    _texture_folder = Path(str(folder))
    _catalog = build_catalog(_texture_folder)
    _loaded_categories.clear()
    refresh_current_textures()


def refresh_current_textures() -> None:
    """Rebuild the CURRENT list from polygon objects only (P<number> meshes).

    Props and car parts are intentionally excluded — they inflate the list with
    hundreds of vehicle textures that are never used on map polygons.
    """
    global _current_items
    try:
        stems: set[str] = set()
        for obj in bpy.data.objects:
            if obj.type != "MESH":
                continue
            # Only consider polygon objects: named P<number> or Shape_<number>
            name = obj.name
            is_polygon = (
                (name.startswith("P") and name[1:].split(".")[0].isdigit())
                or name.startswith("Shape_")
            )
            if not is_polygon:
                continue
            for slot in obj.material_slots:
                mat = slot.material
                if not mat or not mat.use_nodes:
                    continue
                for node in mat.node_tree.nodes:
                    if isinstance(node, bpy.types.ShaderNodeTexImage) and node.image:
                        stem = Path(node.image.name).stem.replace(".DDS", "").replace(".dds", "").upper()
                        stems.add(stem)
        items = [
            (name, make_friendly(name), name)
            for name in sorted(stems)
        ]
        _current_items = items or [("CHECK04", "Checkpoint", "CHECK04")]
    except Exception:
        if not _current_items:
            _current_items = [("CHECK04", "Checkpoint", "CHECK04")]


# ── Enum-item helpers ──────────────────────────────────────────────────────────

def _fallback_items() -> list[tuple]:
    """Minimal fallback so the enum never has zero entries (Blender crashes)."""
    items = []
    for attr_name, dds_name in vars(Texture).items():
        if attr_name.startswith("_") or not isinstance(dds_name, str):
            continue
        label = attr_name.replace("_", " ").title()
        items.append((dds_name, label, dds_name))
    items.sort(key=lambda x: x[1])
    return items


# Blender calls this every time the dropdown is drawn — keep it O(1).
def texture_enum_items(self, context) -> list[tuple]:
    try:
        cat = context.scene.texture_category if context and context.scene else "CURRENT"
    except Exception:
        cat = "CURRENT"

    if cat == "CURRENT":
        return _current_items or _fallback_items()

    if cat == "ALL":
        all_items: list[tuple] = []
        for cat_items in _catalog.values():
            all_items.extend(cat_items)
        all_items.sort(key=lambda x: x[1])
        return all_items or _fallback_items()

    return _catalog.get(cat) or _fallback_items()


# Stable reference required for EnumProperty – must NOT be a lambda or local.
TEXTURE_ENUM_ITEMS = texture_enum_items


# ── Lazy DDS loader ────────────────────────────────────────────────────────────

def _load_category_textures(category: str) -> None:
    """Load DDS images for *category* into bpy.data.images (once per session)."""
    if not _texture_folder or category in _loaded_categories:
        return

    if category == "ALL":
        stems = [item[0] for cat_items in _catalog.values() for item in cat_items]
    elif category == "CURRENT":
        return  # Already loaded during mesh creation
    else:
        stems = [item[0] for item in _catalog.get(category, [])]

    for stem in stems:
        path = _texture_folder / f"{stem}{FileType.DIRECTDRAW_SURFACE}"
        if path.exists() and str(path) not in bpy.data.images:
            bpy.data.images.load(str(path))

    _loaded_categories.add(category)


def category_for_texture(stem: str) -> str:
    """Return the category key that contains *stem*, preferring CURRENT when present."""
    stem = stem.upper()
    # Check CURRENT first (polygon textures the user is already working with)
    if any(item[0] == stem for item in _current_items):
        return "CURRENT"
    # Otherwise use the catalog categorisation
    return categorise(stem)


def update_texture_category(self, context) -> None:
    """Called when the user switches the Texture Category dropdown."""
    cat = getattr(context.scene, "texture_category", "CURRENT")
    if cat == "CURRENT":
        refresh_current_textures()
    else:
        _load_category_textures(cat)


def ensure_category_loaded(cat: str) -> None:
    """Load DDS files for *cat* if not yet done. Safe to call from draw."""
    if cat != "CURRENT":
        _load_category_textures(cat)


class OBJECT_OT_RefreshCurrentTextures(bpy.types.Operator):
    bl_idname   = "object.refresh_current_textures"
    bl_label    = "Refresh"
    bl_description = "Rescan all loaded materials and update the Current texture list"

    def execute(self, context) -> set:
        refresh_current_textures()
        return {"FINISHED"}


# ── Texture-name / UV callbacks ────────────────────────────────────────────────

def update_texture_name(self, context) -> None:
    if not _texture_folder or not self.texture_name:
        return

    def apply(obj) -> None:
        texture_path = _texture_folder / f"{obj.texture_name}{FileType.DIRECTDRAW_SURFACE}"
        if not texture_path.exists():
            return
        _apply_material(obj, obj.texture_name, texture_path)

    def apply_from(obj, tex_name: str) -> None:
        texture_path = _texture_folder / f"{tex_name}{FileType.DIRECTDRAW_SURFACE}"
        if not texture_path.exists():
            return
        _apply_material(obj, tex_name, texture_path)

    apply(self)
    for obj in context.selected_objects:
        if obj.type == "MESH" and obj != self:
            apply_from(obj, self.texture_name)


def _apply_material(obj, material_name: str, texture_path: Path) -> None:
    obj.data.materials.clear()

    if material_name in bpy.data.materials:
        mat = bpy.data.materials[material_name]
    else:
        mat = bpy.data.materials.new(name=material_name)

    obj.data.materials.append(mat)
    obj.active_material = mat
    mat.use_nodes = True

    nodes = mat.node_tree.nodes
    for node in nodes:
        nodes.remove(node)

    diffuse  = nodes.new(type="ShaderNodeBsdfPrincipled")
    tex_node = nodes.new(type="ShaderNodeTexImage")
    tex_node.image = bpy.data.images.load(str(texture_path), check_existing=True)

    links = mat.node_tree.links
    links.new(tex_node.outputs["Color"], diffuse.inputs["Base Color"])
    output = nodes.new(type="ShaderNodeOutputMaterial")
    links.new(diffuse.outputs["BSDF"], output.inputs["Surface"])


def update_uv_tiling(self, context) -> None:
    obj = self
    uv_layer = obj.data.uv_layers.active
    if not uv_layer:
        return

    tile_x = obj.tile_x
    tile_y = obj.tile_y
    angle_degrees = obj.angle_degrees

    base_coords = [(0, 0), (1, 0), (1, 1), (0, 1)]
    center_x, center_y = 0.5, 0.5
    rad = math.radians(angle_degrees)

    computed_uvs = []
    for x, y in base_coords:
        x -= center_x
        y -= center_y
        rx = x * math.cos(rad) - y * math.sin(rad)
        ry = x * math.sin(rad) + y * math.cos(rad)
        computed_uvs.append(((rx + center_x) * tile_x, (ry + center_y) * tile_y))

    for i, uv_data in enumerate(uv_layer.data):
        u, v = computed_uvs[i % len(computed_uvs)]
        uv_data.uv = (u, 1.0 - v)

    obj.data.update()


class OBJECT_OT_UpdateUVMapping(bpy.types.Operator):
    bl_idname   = "object.update_uv_mapping"
    bl_label    = "Update UV Mapping"
    bl_description = "Updates UV mapping based on object's tile and rotation properties"
    bl_options  = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> set:
        for obj in bpy.context.selected_objects:
            if obj.type != "MESH":
                continue
            update_uv_tiling(obj, context)
        return {"FINISHED"}
