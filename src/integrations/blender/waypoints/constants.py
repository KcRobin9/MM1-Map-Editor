POLE_HEIGHT        = 3.0
POLE_DIAMETER      = 0.2
FLAG_HEIGHT        = 0.8
FLAG_HEIGHT_OFFSET = 2.2

FLAG_TEXTURE = "CHECK_POINT_02.DDS"
IMG_PREFIX   = "WP_Flag_"
MAT_PREFIX   = "WP_FlagMat_"


class FlagUV:
    CHECKPOINT = "CHECKPOINT"
    FINISH     = "FINISH"
    BANK       = "BANK"
    HIDEOUT    = "HIDEOUT"

# Pixel row bands in the source DDS (Blender pixels: row 0 = bottom)
FLAG_BANDS = {
    FlagUV.CHECKPOINT: (0,   256),
    FlagUV.FINISH:     (256, 512),
    FlagUV.BANK:       (512, 768),
    FlagUV.HIDEOUT:    (768, 1024),
}