"""
Vehicle Showcase image generator (Blender render → game JPG).

The picker's "Vehicle Showcase" screen is a single 640×480 JPG named
`BMP16/{CAR}_SHOW.JPG` (game builds the name via the `%s_show` format), stored
UPSIDE-DOWN (the game flips on display).

We reproduce the stock look by compositing the live car render onto a template
derived from a real stock frame (`resources/editor/SHOWCASE_TEMPLATE.png` — the
authentic bold-serif title + olive frame + sky-backed photo box, with the stock
car photo and text cleared):

  1. Blender renders the car (Workbench TEXTURE shading, transparent film) from a
     3/4 front hero angle.
  2. Pillow pastes the trimmed car into the photo box and draws the name + specs.

Pillow is required (add it via setup/blender_python_libraries.txt → run the
installer); the rest of the Car Editor works without it.
"""
import math
import importlib.util
from pathlib import Path

import bpy
import mathutils

from src.constants.folder import Folder

SHOWCASE_W = 640
SHOWCASE_H = 480

_TEMPLATE = Folder.Resources.Editor.Root / "SHOWCASE_TEMPLATE.png"

# Layout in template pixel space (right-side-up).
_PHOTO_BOX = (306, 76, 622, 310)     # inside the stock blue photo border
_NAME_XY   = (30, 132)
_NAME_MAXW = 250                     # wrap the car name within this width
_SPEC_X    = 30
_SPEC_Y    = 150                     # floor for the spec block (it normally hugs the name)
_SPEC_LH   = 23
_NAME_COL  = (38, 36, 66)            # dark navy — reads on the bright olive band
_SPEC_COL  = (232, 233, 214)         # cream — reads on the dark olive panel
_PANEL_COL = (92, 89, 8)             # dark olive spec panel (drawn at runtime)


# ── Blender car render ──────────────────────────────────────────────────────

def _frame_camera(cam_obj, objs, direction, margin: float = 1.18):
    """Aim a perspective camera at the car's bbox centre from `direction`, backed
    off so the bounding sphere fits the vertical FOV."""
    pts = []
    for o in objs:
        for c in o.bound_box:
            pts.append(o.matrix_world @ mathutils.Vector(c))
    if not pts:
        return
    mn = mathutils.Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = mathutils.Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    centre = (mn + mx) * 0.5
    radius = max((p - centre).length for p in pts)

    d = mathutils.Vector(direction).normalized()
    dist = (radius / math.sin(cam_obj.data.angle * 0.5)) * margin
    cam_obj.location = centre + d * dist
    look = (centre - cam_obj.location).normalized()
    cam_obj.rotation_euler = look.to_track_quat("-Z", "Y").to_euler()


def _render_car_png(car_objects, png_path: Path) -> None:
    """Render the car to an RGBA PNG with a transparent background."""
    sc = bpy.data.scenes.new("_showcase_car")
    cam = None
    try:
        r = sc.render
        r.resolution_x = 600
        r.resolution_y = 450
        r.resolution_percentage = 100
        r.film_transparent = True
        r.engine = "BLENDER_WORKBENCH"
        r.image_settings.file_format = "PNG"
        r.image_settings.color_mode = "RGBA"

        sh = sc.display.shading
        sh.light = "STUDIO"
        sh.color_type = "TEXTURE"
        sh.show_shadows = True
        sh.show_cavity = True

        for o in car_objects:
            sc.collection.objects.link(o)

        cam_data = bpy.data.cameras.new("sc_pcam")
        cam_data.angle = math.radians(32.0)
        cam = bpy.data.objects.new("sc_pcam", cam_data)
        sc.collection.objects.link(cam)
        sc.camera = cam
        # -Y is the car's front in Blender; +X side, +Z up → 3/4 front hero angle.
        _frame_camera(cam, car_objects, direction=(0.9, -1.15, 0.5))

        r.filepath = str(png_path)
        bpy.ops.render.render(write_still=True, scene=sc.name)
    finally:
        if cam is not None:
            cdata = cam.data
            bpy.data.objects.remove(cam, do_unlink=True)
            if cdata and cdata.users == 0:
                bpy.data.cameras.remove(cdata)
        bpy.data.scenes.remove(sc)


# ── Pillow compositing ──────────────────────────────────────────────────────

def _font(size: int, bold: bool):
    from PIL import ImageFont
    cands = (["C:/Windows/Fonts/arialbd.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"]
             if bold else
             ["C:/Windows/Fonts/arial.ttf", "arial.ttf", "DejaVuSans.ttf"])
    for c in cands:
        try:
            return ImageFont.truetype(c, size)
        except Exception:
            pass
    return ImageFont.load_default()


def _wrap(draw, text: str, font, max_w: int):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if draw.textlength(trial, font=font) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [""]


def _autocrop_alpha(img):
    bbox = img.split()[3].getbbox()
    return img.crop(bbox) if bbox else img


def _compose(car_png: Path, info: dict, out_path: Path, preview_path):
    from PIL import Image, ImageDraw, ImageOps, ImageFilter

    base = Image.open(_TEMPLATE).convert("RGB")
    car = _autocrop_alpha(Image.open(car_png).convert("RGBA"))

    bx0, by0, bx1, by1 = _PHOTO_BOX
    bw, bh = bx1 - bx0, by1 - by0
    car.thumbnail((int(bw * 0.96), int(bh * 0.96)), Image.LANCZOS)
    cx = bx0 + (bw - car.width) // 2
    cy = by1 - car.height - int(bh * 0.07)        # ground the car near the box floor

    # Soft contact shadow so the car doesn't float (kept inside the photo box).
    scx = cx + car.width // 2
    scy = cy + car.height - 4
    sw = int(car.width * 0.78)
    shadow = Image.new("L", base.size, 0)
    ImageDraw.Draw(shadow).ellipse(
        [scx - sw // 2, scy - 9, scx + sw // 2, scy + 9], fill=130)
    shadow = shadow.filter(ImageFilter.GaussianBlur(5))
    base.paste((0, 0, 0), (0, 0), shadow)

    base.paste(car, (cx, cy), car)

    draw = ImageDraw.Draw(base)

    name_font = _font(30, bold=True)
    ny = _NAME_XY[1]
    for line in _wrap(draw, info.get("name", ""), name_font, _NAME_MAXW):
        draw.text((_NAME_XY[0], ny), line, font=name_font, fill=_NAME_COL)
        ny += 34

    # Dark spec panel drawn to hug the name (no empty gap for short names), then
    # cream specs on top.  L-shaped: narrow beside the photo box, wider below it.
    specs = info.get("specs", [])
    spec_top = max(_SPEC_Y, ny + 40)
    panel_bottom = spec_top + len(specs) * _SPEC_LH + 8
    box_bottom = _PHOTO_BOX[3]
    if spec_top < box_bottom:
        draw.rectangle([14, spec_top - 8, 302, min(box_bottom, panel_bottom)], fill=_PANEL_COL)
    if panel_bottom > box_bottom:
        draw.rectangle([14, box_bottom, 455, panel_bottom], fill=_PANEL_COL)

    spec_font = _font(15, bold=False)
    y = spec_top
    for label, value in specs:
        draw.text((_SPEC_X, y), f"{label}:  {value}", font=spec_font, fill=_SPEC_COL)
        y += _SPEC_LH

    # Game file is stored upside-down (game flips on display); preview stays upright.
    ImageOps.flip(base).save(str(out_path), "JPEG", quality=92)
    if preview_path is not None:
        base.save(str(preview_path), "JPEG", quality=92)


# ── public API ──────────────────────────────────────────────────────────────

def generate_showcase(car_objects, info: dict, out_path: Path, tmp_dir: Path,
                      preview_path: Path = None) -> Path:
    """Render the car and compose a stock-style showcase JPG at `out_path`.

    `info` keys: 'name' (str), 'specs' (list of (label, value)).
    `out_path` gets the game-ready (upside-down) JPG; `preview_path` (optional)
    gets an upright copy for the user.  Requires Pillow.
    """
    if importlib.util.find_spec("PIL") is None:
        raise RuntimeError(
            "Pillow is not installed in Blender's Python. Add 'Pillow' and run "
            "setup/blender_python_libraries.txt (the installer)."
        )

    out_path = Path(out_path).resolve()
    tmp_dir = Path(tmp_dir).resolve()
    tmp_dir.mkdir(parents=True, exist_ok=True)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if preview_path is not None:
        Path(preview_path).parent.mkdir(parents=True, exist_ok=True)

    car_png = tmp_dir / "_sc_car.png"
    _render_car_png(car_objects, car_png)
    _compose(car_png, info, out_path, preview_path)
    return out_path
