"""
Pure VPMUSTANG99 pack test — no Blender, no custom init code.

Copies every VPMUSTANG99 file verbatim into SHOP, renames to CAR_NAME,
then packs !!!!!{CAR_NAME}.ar using mkar.

This is the minimum viable isolation test:
  - body  = original VPMUSTANG99 BODY_H.BMS (unmodified)
  - WHL   = original VPMUSTANG99 WHL0-3_H.BMS + _M copies (unmodified)
  - TSH   = original VPMUSTANG99.TSH (so neighbourhood = v4, not 'car')
  - TUNE  = original VPMUSTANG99 TUNE files
  - BND   = original VPMUSTANG99_BND.BND

If wheels show in-game after this test, the pipeline is correct and only
our custom TSH / init code needs fixing.
If wheels still don't show, the problem is deeper (mkar / game config).

Usage:
    python development/test_pure_mustang_pack.py [CAR_NAME]
    default CAR_NAME = VPTEST
"""
import shutil
import subprocess
import sys
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE       = Path(__file__).parent.parent.resolve()
CORE       = BASE / "core"
SHOP       = BASE / "SHOP"
MM1        = BASE / "MidtownMadness"
MKAR       = BASE / "angel" / "mkar.exe"

CAR_NAME   = (sys.argv[1].upper() if len(sys.argv) > 1 else "VPTEST")
SOURCE     = "VPMUSTANG99"
AR_OUT     = MM1 / f"!!!!!{CAR_NAME}.ar"
TMP        = BASE / f"_pack_tmp_{CAR_NAME}"

BMS_SUPPORT = [
    "BLIGHT.BMS",
    "HLIGHT_H.BMS",
    "RLIGHT.BMS",
    "SHADOW_H.BMS",
    "SLIGHT0.BMS",
    "SLIGHT1.BMS",
    "TLIGHT.BMS",
]


def _cp(src: Path, dst: Path) -> None:
    if not src.exists():
        print(f"  MISSING: {src}")
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"  {src.name} -> {dst.relative_to(BASE)}")


def setup_shop() -> None:
    print(f"\n=== Setting up SHOP for {CAR_NAME} (source: {SOURCE}) ===\n")

    # BMS: body + lights + shadow (no WHL — sourced from core at pack time)
    bms_src = CORE / "BMS" / SOURCE
    bms_dst = SHOP / "BMS" / CAR_NAME
    if bms_dst.exists():
        shutil.rmtree(bms_dst)
    bms_dst.mkdir(parents=True)

    _cp(bms_src / "BODY_H.BMS", bms_dst / "BODY_H.BMS")
    shutil.copy2(bms_dst / "BODY_H.BMS", bms_dst / "BODY_M.BMS")  # mmDamage::InitDamage needs Meshes[2]
    _cp(bms_src / "H.BMS",      bms_dst / "H.BMS")        # car picker
    for fname in BMS_SUPPORT:
        _cp(bms_src / fname, bms_dst / fname)

    # TUNE: copy all VPMUSTANG99* files, rename prefix to CAR_NAME
    tune_src = CORE / "TUNE"
    tune_dst = SHOP / "TUNE"
    tune_dst.mkdir(parents=True, exist_ok=True)
    n = 0
    for f in sorted(tune_src.iterdir()):
        if f.is_file() and f.name.upper().startswith(SOURCE):
            new_name = CAR_NAME + f.name[len(SOURCE):]
            shutil.copy2(f, tune_dst / new_name)
            print(f"  {f.name} -> SHOP/TUNE/{new_name}")
            n += 1
    print(f"  {n} TUNE files copied")

    # .INFO — game discovers the car via this file
    info = tune_dst / f"{CAR_NAME}.INFO"
    info.write_text(
        f"BaseName={CAR_NAME}\n"
        f"Description=Test ({SOURCE} clone)\n"
        f"Colors=Red\n"
        f"Flags=0\n"
        f"Order=-1\n"
        f"ScoringBias=5.0\n"
        f"UnlockScore=0\n"
        f"UnlockFlags=0\n"
        f"Horsepower=320\n"
        f"Top Speed=200\n"
        f"Durability=500000\n"
        f"Mass=1500\n",
        encoding="ascii",
    )
    print(f"  wrote SHOP/TUNE/{CAR_NAME}.INFO")

    # TSH — use the ORIGINAL VPMUSTANG99.TSH verbatim (neighbourhood = v4)
    tsh_src = CORE / "MTL" / f"{SOURCE}.TSH"
    tsh_dst = SHOP / "MTL" / f"{CAR_NAME}.TSH"
    tsh_dst.parent.mkdir(parents=True, exist_ok=True)
    _cp(tsh_src, tsh_dst)

    # BND
    bnd_src = CORE / "BND" / f"{SOURCE}_BND.BND"
    bnd_dst = SHOP / "BND" / f"{CAR_NAME}_BND.BND"
    bnd_dst.parent.mkdir(parents=True, exist_ok=True)
    _cp(bnd_src, bnd_dst)

    # TEX16A — VPCOP_WHL wheel texture
    tex_src  = CORE / "TEX16A" / "VPCOP_WHL.DDS"
    if not tex_src.exists():
        # Fallback: check resources/editor/TEXTURES
        tex_src = BASE / "resources" / "editor" / "TEXTURES" / "VPCOP_WHL.DDS"
    tex_dst  = SHOP / "TEX16A" / "VPCOP_WHL.DDS"
    tex_dst.parent.mkdir(parents=True, exist_ok=True)
    _cp(tex_src, tex_dst)

    # DLP — GetDLPTemplate("VPAAA") reads dlp/VPAAA.dlp at runtime for wheel
    # center positions (FrontLeft.Center etc).  Without it, Center=(0,0,0) and
    # all wheels render at the car's origin, invisible inside the body.
    dlp_src = CORE / "DLP" / f"{SOURCE}.DLP"
    dlp_dst = SHOP / "DLP" / f"{CAR_NAME}.DLP"
    dlp_dst.parent.mkdir(parents=True, exist_ok=True)
    _cp(dlp_src, dlp_dst)


def pack_ar() -> bool:
    print(f"\n=== Packing {AR_OUT.name} ===\n")

    if not MKAR.exists():
        print(f"ERROR: mkar.exe not found at {MKAR}")
        return False

    if TMP.exists():
        shutil.rmtree(TMP)
    TMP.mkdir(parents=True)

    # BMS/{CAR_NAME}/ — body + support files
    bms_shop = SHOP / "BMS" / CAR_NAME
    bms_tmp  = TMP / "BMS" / CAR_NAME
    bms_tmp.mkdir(parents=True)
    for f in sorted(bms_shop.iterdir()):
        if f.is_file() and not f.name.upper().startswith("WHL"):
            shutil.copy2(f, bms_tmp / f.name)
            print(f"  BMS/{CAR_NAME}/{f.name}")

    # WHL from core (original, unmodified)
    whl_core = CORE / "BMS" / SOURCE
    for i in range(4):
        src = whl_core / f"WHL{i}_H.BMS"
        if not src.exists():
            break
        shutil.copy2(src, bms_tmp / f"WHL{i}_H.BMS")
        shutil.copy2(src, bms_tmp / f"WHL{i}_M.BMS")
        print(f"  BMS/{CAR_NAME}/WHL{i}_H+M.BMS  <- core/{SOURCE}/")

    # TUNE/
    tune_tmp = TMP / "TUNE"
    tune_tmp.mkdir()
    for f in sorted((SHOP / "TUNE").iterdir()):
        if f.is_file() and f.name.upper().startswith(CAR_NAME):
            shutil.copy2(f, tune_tmp / f.name)
            print(f"  TUNE/{f.name}")

    # MTL/
    tsh = SHOP / "MTL" / f"{CAR_NAME}.TSH"
    if tsh.exists():
        mtl_tmp = TMP / "MTL"
        mtl_tmp.mkdir()
        shutil.copy2(tsh, mtl_tmp / tsh.name)
        print(f"  MTL/{tsh.name}")

    # BND/
    bnd = SHOP / "BND" / f"{CAR_NAME}_BND.BND"
    if bnd.exists():
        bnd_tmp = TMP / "BND"
        bnd_tmp.mkdir()
        shutil.copy2(bnd, bnd_tmp / bnd.name)
        print(f"  BND/{bnd.name}")

    # TEX16A/
    tex_shop = SHOP / "TEX16A"
    tex_files = [f for f in tex_shop.iterdir() if f.is_file() and f.suffix.upper() == ".DDS"]
    if tex_files:
        tex_tmp = TMP / "TEX16A"
        tex_tmp.mkdir()
        for f in tex_files:
            shutil.copy2(f, tex_tmp / f.name)
            print(f"  TEX16A/{f.name}")

    # DLP/
    dlp = SHOP / "DLP" / f"{CAR_NAME}.DLP"
    if dlp.exists():
        dlp_tmp = TMP / "DLP"
        dlp_tmp.mkdir()
        shutil.copy2(dlp, dlp_tmp / dlp.name)
        print(f"  DLP/{dlp.name}")

    # Shiplist
    pack_files = sorted(f for f in TMP.rglob("*") if f.is_file())
    lines = [f"./{f.relative_to(TMP).as_posix()}" for f in pack_files]
    shiplist = TMP / f"shiplist.{CAR_NAME}"
    shiplist.write_bytes(("\n".join(lines) + "\n").encode("ascii"))

    print(f"\n  Packing {len(pack_files)} files …")
    result = subprocess.run(
        [str(MKAR), str(AR_OUT), str(shiplist)],
        cwd=str(TMP),
        capture_output=True,
        text=True,
    )
    if result.stdout:
        print(f"  mkar: {result.stdout.strip()}")
    if result.stderr:
        print(f"  mkar: {result.stderr.strip()}")

    ok = result.returncode == 0
    if ok:
        print(f"\n  Created: {AR_OUT}")
    else:
        print(f"\n  ERROR: mkar exit {result.returncode}")

    try:
        shutil.rmtree(TMP)
    except OSError:
        pass

    return ok


if __name__ == "__main__":
    print(f"Car name : {CAR_NAME}")
    print(f"Source   : {SOURCE}")
    print(f"AR output: {AR_OUT}")

    setup_shop()
    ok = pack_ar()

    if ok:
        print(f"\nDone. Launch MM1 and select '{CAR_NAME}' to test.")
        print("If wheels are visible  => packing pipeline is correct.")
        print("If wheels are missing  => deeper issue (game config / TSH namespace).")
    else:
        print("\nPack failed. Check errors above.")
        sys.exit(1)
