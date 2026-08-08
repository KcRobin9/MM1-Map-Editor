"""Texture/TSH validation operator — surfaces the bpy-free audit in Blender.

Catches the most common in-game failure ("loads but invisible/black"): a BMS in the
built SHOP references a texture that has no DDS, or has a DDS that no TSH declares, or
is an alpha texture sitting in the opaque (TEX16O) folder. Run it after building the
map or packing a car, before launching.
"""
import bpy

from src.constants.folder import Folder
from src.integrations.blender.modeling.texture_audit import audit_textures, format_report


class OBJECT_OT_AuditMapTextures(bpy.types.Operator):
    bl_idname      = "object.audit_map_textures"
    bl_label       = "Audit Textures (SHOP)"
    bl_description = ("Check every texture referenced by the built BMS in SHOP is declared in a "
                      "TSH and present as a DDS. Full report to debug/output/texture_audit.txt")
    bl_options     = {"REGISTER"}

    def execute(self, context):
        shop_bms = Folder.Shop.Meshes
        if not shop_bms.is_dir() or not any(shop_bms.rglob("*.BMS")):
            self.report({"ERROR"}, "No built BMS in SHOP/BMS - build the map or pack a car first.")
            return {"CANCELLED"}

        map_tsh = sorted(Folder.Shop.Material.glob("*.TSH")) if Folder.Shop.Material.is_dir() else []
        tex_folders = [
            ("TEX16A", Folder.Shop.Textures.Alpha),
            ("TEX16O", Folder.Shop.Textures.Opaque),
            ("resources", Folder.Resources.Editor.Textures),
        ]
        report = audit_textures(shop_bms, map_tsh, Folder.Resources.Editor.MTL / "GLOBAL.TSH",
                                tex_folders, packed_labels={"TEX16A", "TEX16O"})

        text = format_report(report)
        print("[Texture Audit]\n" + text)

        out_dir = Folder.Debug.Output
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "texture_audit.txt").write_text(text, encoding="ascii", errors="replace")

        n_err = len(report["missing"])
        n_warn = len(report["undeclared"]) + len(report["alpha_split"])
        level = "ERROR" if n_err else ("WARNING" if n_warn else "INFO")
        self.report({level}, f"{report['ok']}/{report['referenced']} OK, {n_err} missing, "
                             f"{n_warn} warnings - see debug/output/texture_audit.txt")
        return {"FINISHED"}


VALIDATE_TEXTURES_CLASSES = [
    OBJECT_OT_AuditMapTextures,
]
