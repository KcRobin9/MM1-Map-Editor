class Quality:
    LOW       = 0
    MEDIUM    = 1
    HIGH      = 2
    VERY_HIGH = 3


class Shadows:
    OFF       = 0
    VEHICLES  = 1
    PROPS     = 2
    SKIDMARKS = 3


class Camera:
    BUMPER    = 0
    HOOD      = 1
    FAR       = 2
    TOP       = 3
    CINEMATIC = 4
    NAMES     = {0: "Bumper", 1: "Hood", 2: "Far", 3: "Top", 4: "Cinematic"}


class InputType:
    MOUSE     = 0 
    KEYBOARD  = 1 
    JOYSTICK  = 2 
    NAMES     = {0: "Mouse", 1: "Keyboard", 2: "Joystick"}


class Transmission:
    MANUAL = 0
    AUTO   = 1


class HudMap:
    NONE   = 0  
    SMALL  = 1 
    MEDIUM = 2  
    LARGE  = 3 


class AudioFlags:
    SFX        = 1 << 0
    CD_MUSIC   = 1 << 1
    HI_RES     = 1 << 2
    STEREO     = 1 << 3
    HI_SAMPLE  = 1 << 4
    COMMENTARY = 1 << 5
    DEFAULT    = SFX | CD_MUSIC | HI_RES | COMMENTARY  # 0b100111


class Progress:
    NONE = 0x000
    ALL  = 0xFFF  # all 12 races unlocked (12-bit bitmask, 1 bit per race)


NUM_IODEV_SLOTS   = 165  # 5 groups x 33 actions (IODEV_NUM_CONFIGS x IOID_COUNT)
IODEV_NUM_CONFIGS = 5
IOID_COUNT        = 33


class IoType:
    DISCRETE   = 1  # key / button
    CONTINUOUS = 2  # mouse / joystick axis
    EVENT      = 3  # tap / toggle


class IODevice:
    MOUSE     = 2
    KEYBOARD  = 3
    JOYSTICK1 = 4
    JOYSTICK2 = 5
    JOYSTICK3 = 6


class JoyInput:
    # mmJoyInput — mouse buttons (EQ_BUTTON_*)
    M_BUTTON_LEFT  = 1
    M_BUTTON_RIGHT = 2
    # mmJoyInput — axes
    XAXIS       = 10
    YAXIS       = 11
    ZAXIS       = 12
    UAXIS       = 13
    RAXIS       = 14
    VAXIS       = 15
    POV_AXIS    = 16
    XAXIS_LEFT  = 17
    XAXIS_RIGHT = 18
    YAXIS_UP    = 19
    YAXIS_DOWN  = 20
    # mmJoyInput — joystick buttons
    BUTTON_1    = 21
    BUTTON_2    = 22
    BUTTON_3    = 23
    BUTTON_4    = 24
    BUTTON_5    = 25
    BUTTON_6    = 26
    BUTTON_7    = 27
    BUTTON_8    = 28
    BUTTON_9    = 29
    ZAXIS_UP    = 33
    ZAXIS_DOWN  = 34


# DirectInput scan codes — Open1560 eventq7/keys.h (EQ_KEY_*)
class ScanCode:
    ESC      = 0x01
    NUM_1    = 0x02
    NUM_2    = 0x03
    NUM_3    = 0x04
    NUM_4    = 0x05
    NUM_5    = 0x06
    NUM_6    = 0x07
    NUM_7    = 0x08
    NUM_8    = 0x09
    NUM_9    = 0x0A
    NUM_0    = 0x0B
    BACK     = 0x0E  # Backspace
    TAB      = 0x0F
    Q        = 0x10
    W        = 0x11
    E        = 0x12
    R        = 0x13
    T        = 0x14
    Y        = 0x15
    U        = 0x16
    I        = 0x17
    O        = 0x18
    P        = 0x19
    RETURN   = 0x1C  # Enter
    A        = 0x1E
    S        = 0x1F
    D        = 0x20
    H        = 0x23
    Z        = 0x2C
    X        = 0x2D
    C        = 0x2E
    V        = 0x2F
    SPACE    = 0x39
    NUMPAD8  = 0x48
    NUMPAD4  = 0x4B
    NUMPAD6  = 0x4D
    NUMPAD2  = 0x50
    UP       = 0xC8  # Up arrow    (extended, distinct from Numpad 8)
    DOWN     = 0xD0  # Down arrow  (extended, distinct from Numpad 2)
    LEFT     = 0xCB  # Left arrow  (extended)
    RIGHT    = 0xCD  # Right arrow (extended)