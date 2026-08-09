"""
MM2 PKG model parser (PKG3/PKG2). PKG files hold the 3D geometry + materials of MM2 props/monuments/
detailed buildings (placed by INST/PSDL/Pathset). We parse the geometry (per-section triangles with UVs)
and the shader texture names so the detailed BUILDING meshes can be baked into the MM1 city.

Spec: angel-file-formats 'Midtown Madness 2/PKG.md'. Structure:
  "PKG3" then a list of FILE chunks: "FILE", String name, (PKG3: int length), data.
  geometry chunk (name suffix VL/L/M/H = LOD): n_sections,n_verts_total,n_indices_total,_,fvf, then
    sections[n_strips,flags,shader_offset, strips[_,_, verts[fvf], _, indices[u16]]].
  "shaders" chunk: shader_type(bit7=kind,bit0-6=#paintjobs), shaders_per_paint_job, shaders[name,...].
  vertex (per fvf bits): XYZ(0x002)=pos3f, NORMAL(0x010)=3f, TEX1(0x100)=uv2f.
"""
from typing import Dict, List
from pathlib import Path

from src.io.binary import read_unpack

FVF_POSITION = 0x002
FVF_NORMAL   = 0x010
FVF_TEXCOORD = 0x100

LIGHT_SHADER_BLOCK = 16     # 3 * Color4d + shininess
FULL_SHADER_BLOCK  = 68     # 4 * Color4f + shininess

CHUNK_MARKER = b"FILE"
LOD_SUFFIXES = ("VL", "L", "M", "H")

PAINT_JOB_MASK   = 0x7F     # low bits of shader_type = paint-job count
LIGHT_SHADER_BIT = 0x80


def _read_string(f) -> str:
    """A length-prefixed name; the stored length counts the terminator, so the last byte is dropped.

    Only the trailing byte goes: a few MM2 shader names carry embedded NULs (sky_dome_lost's
    "skylost_ca_l\\x00\\x00") and those are part of the key the texture lookup matches on.
    """
    length, = read_unpack(f, "<B")

    return f.read(length)[:-1].decode("latin-1", "ignore")


def parse_pkg(path: str, lod: str = "H") -> Dict:
    """Parse a .pkg into {lods, sections, shader_tex}. `lod` picks which LOD's sections come back."""
    with open(path, "rb") as f:
        f.seek(0, 2)
        size = f.tell()
        f.seek(0)

        magic = f.read(4)
        if magic not in (b"PKG3", b"PKG2"):
            raise ValueError(f"not a PKG: {path}")
        is_pkg3 = (magic == b"PKG3")

        geometries: Dict[str, List] = {}    # lod name -> [(shader_offset, [(pos, uv) triangles])]
        shader_textures: List[str] = []     # paint-job-0 texture names, indexed by shader_offset

        while f.tell() + 4 <= size and f.read(4) == CHUNK_MARKER:
            name = _read_string(f)
            length, = read_unpack(f, "<i") if is_pkg3 else (0,)

            body = f.tell()
            upper = name.upper()

            try:
                if upper.endswith(LOD_SUFFIXES):
                    geometries[upper] = _parse_geometry(f)
                elif name == "shaders":
                    shader_textures = _parse_shaders(f)
            except Exception:
                pass                    # a malformed chunk must not lose the rest of the file

            # Only PKG3 chunks carry their data size, so only they can be stepped over reliably.
            # Without one there is nothing to seek to, and the walk stops at the next non-FILE
            # marker -- so a PKG2 file yields its first chunk only. Note the chunk parsers above
            # move the cursor themselves, hence the explicit seek back to `body` here.
            f.seek(body + length if (is_pkg3 and length > 0) else body)

    return {
        "lods":        list(geometries),
        "sections":    geometries.get(lod.upper()) or (list(geometries.values()) or [[]])[0],
        "shader_tex":  shader_textures,
    }


def _parse_geometry(f) -> List:
    n_sections, _, _, _, fvf = read_unpack(f, "<5i")

    position_floats = 3 if fvf & FVF_POSITION else 0
    normal_floats   = 3 if fvf & FVF_NORMAL else 0
    vertex_floats   = position_floats + normal_floats + (2 if fvf & FVF_TEXCOORD else 0)
    uv_offset       = position_floats + normal_floats
    has_uv          = bool(fvf & FVF_TEXCOORD)

    sections = []
    for _ in range(n_sections):
        n_strips, _ = read_unpack(f, "<2H")
        shader_offset, = read_unpack(f, "<i")

        triangles = []
        for _ in range(n_strips):
            _, n_verts = read_unpack(f, "<2i")
            verts = read_unpack(f, f"<{n_verts * vertex_floats}f")
            n_indices, = read_unpack(f, "<i")
            indices = read_unpack(f, f"<{n_indices}H")

            def vertex(i: int):
                base = i * vertex_floats
                position = (verts[base], verts[base + 1], verts[base + 2])
                uv = (verts[base + uv_offset], verts[base + uv_offset + 1]) if has_uv else (0.0, 0.0)
                return position, uv

            for k in range(0, len(indices) - 2, 3):          # primType 3 = triangle list
                triangles.append((vertex(indices[k]), vertex(indices[k + 1]), vertex(indices[k + 2])))

        sections.append((shader_offset, triangles))

    return sections


def _parse_shaders(f) -> List[str]:
    shader_type, per_paint_job = read_unpack(f, "<2i")

    paint_jobs = shader_type & PAINT_JOB_MASK
    is_light = bool(shader_type & LIGHT_SHADER_BIT)
    block_size = LIGHT_SHADER_BLOCK if is_light else FULL_SHADER_BLOCK

    names = []
    for index in range(max(per_paint_job, paint_jobs * per_paint_job)):
        texture = _read_string(f)
        f.seek(block_size, 1)                                # colour / shininess block
        if index < per_paint_job:                            # paint job 0 is what shader_offset indexes
            names.append(texture)

    return names


if __name__ == "__main__":
    import sys

    parsed = parse_pkg(sys.argv[1])
    triangle_count = sum(len(tris) for _, tris in parsed["sections"])
    print("[PKG]", Path(sys.argv[1]).name, "LODs:", parsed["lods"], "sections:", len(parsed["sections"]),
          "triangles:", triangle_count, "shaders:", parsed["shader_tex"])

    if parsed["sections"]:
        shader_offset, triangles = parsed["sections"][0]
        texture = parsed["shader_tex"][shader_offset] if shader_offset < len(parsed["shader_tex"]) else "?"
        print("[PKG] section0 shader_offset:", shader_offset, "tex:", texture)
        print("[PKG] first tri:", triangles[0] if triangles else None)
