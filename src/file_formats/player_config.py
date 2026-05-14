"""
Player config (.cfg) reader/writer.
Mirrors mmPlayerConfig::SaveBinary/LoadBinary (Open1560 mmcityinfo/playercfg.cpp).

Binary layout (2147 bytes):
  i32  Type=1234  i32  Version=18
  f32  WavVol  f32  CDVol  f32  Balance
  u32  Flags (bit0=SFX bit1=CDMusic bit2=HiRes bit3=Stereo bit4=HiSample bit5=Commentary)
  u32  Channels  i32  DeviceNameLen  char DeviceName[DeviceNameLen]
  u32x6  Tex Obj Shadows EnvMap SphrMap Sky
  f32x3  FarClip LightQuality Particles
  u32x4  DisablePeds Interlaced SpeedLoading TexFilter
  i32  InputType  u32  Transmission  f32  PhysicsReal
  u32x2  AutoReverse UsePOVHat  u32  UseForceFB
  f32x7  FFScale RoadForce MouseSens JoyDeadZone SteerDelta SteerLimit SteerSens
  165 x mmIODev (12 bytes: i32 IoType, i32 Device, i32 Component)
  10 x i8  CameraIndex HudmapMode WideView DashView EnableMirror ExternalView XcamView IconsState MapRes pad
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from src.io.binary import read_unpack, write_pack, read_binary_name
from src.constants.misc import Encoding
from src.constants.constants import ON, OFF
from src.constants.menu import (
    Camera, InputType, Transmission, Quality, Shadows, HudMap,
    NUM_IODEV_SLOTS, IoType, IODevice, JoyInput, ScanCode,
)

# Default IODev bindings from a real Chicago install (player0.cfg).
# 165 slots = 5 groups × 33 actions.  Each tuple: (IoType, Device, Component)
#   IoType  : 1=Discrete  2=Continuous  3=Event
#   Device  : 2=Mouse  3=Keyboard  4=Joystick1
#   Component (keyboard): DirectInput scan code
#   Component (mouse/joy): mmJoyInput enum  (Xaxis=10, POVaxis=16, LBtn=1, RBtn=2, ...)
# Action slot indices defined in mminput/input.h (IOID_*):
#   0=MAP  1=FMAP  2=MAPRES  3=HUD  4=STR  5=STRL  6=STRR  7=THROT  8=BRAKE  9=HAND
#   10=CAM  11=XVIEW  12=HORN  13=LOKL  14=LOKR  15=LOKB  16=LOKF  17=WFOV  18=DASH
#   19=TRANS  20=UPSH  21=DWNS  22=REV  23=WYPTN  24=WYPTP
#   25=CDSHOW  26=CDPLAY  27=CDPRIOR  28=CDNEXT  29=MIRROR  30=PAN  31=OPPPOS  32=CHAT

_DEFAULT_IO_DEVS: List[tuple] = [
    # -- group 0: keyboard + mouse (InputConfiguration=0, game default) --
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.TAB),            # MAP     [Tab]        toggle minimap on/off
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.Q),              # FMAP    [Q]          switch to fullscreen map
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.E),              # MAPRES  [E]          cycle minimap resolution
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.H),              # HUD     [H]          toggle HUD display
    (IoType.CONTINUOUS, IODevice.MOUSE,     JoyInput.XAXIS),          # STR     [Mouse X]    continuous steering axis
    (IoType.DISCRETE,   IODevice.KEYBOARD,  ScanCode.LEFT),           # STRL    [← Arrow]    steer left (discrete)
    (IoType.DISCRETE,   IODevice.KEYBOARD,  ScanCode.RIGHT),          # STRR    [→ Arrow]    steer right (discrete)
    (IoType.DISCRETE,   IODevice.MOUSE,     JoyInput.M_BUTTON_LEFT),  # THROT   [LMB]        throttle (hold)
    (IoType.DISCRETE,   IODevice.MOUSE,     JoyInput.M_BUTTON_RIGHT), # BRAKE   [RMB]        brakes (hold)
    (IoType.DISCRETE,   IODevice.KEYBOARD,  ScanCode.SPACE),          # HAND    [Space]      handbrake
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.C),              # CAM     [C]          cycle camera view
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.V),              # XVIEW   [V]          toggle external camera
    (IoType.DISCRETE,   IODevice.KEYBOARD,  ScanCode.RETURN),         # HORN    [Enter]      sound horn
    (IoType.DISCRETE,   IODevice.KEYBOARD,  ScanCode.NUMPAD4),        # LOKL    [Numpad 4]   look left
    (IoType.DISCRETE,   IODevice.KEYBOARD,  ScanCode.NUMPAD6),        # LOKR    [Numpad 6]   look right
    (IoType.DISCRETE,   IODevice.KEYBOARD,  ScanCode.NUMPAD2),        # LOKB    [Numpad 2]   look back
    (IoType.DISCRETE,   IODevice.KEYBOARD,  ScanCode.NUMPAD8),        # LOKF    [Numpad 8]   look forward
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.W),              # WFOV    [W]          toggle wide-angle FOV
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.D),              # DASH    [D]          toggle dashboard view
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.T),              # TRANS   [T]          toggle transmission mode
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.A),              # UPSH    [A]          shift up (manual gearbox)
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.Z),              # DWNS    [Z]          shift down (manual gearbox)
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.R),              # REV     [R]          toggle reverse gear
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.S),              # WYPTN   [S]          next waypoint
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.X),              # WYPTP   [X]          previous waypoint
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.NUM_2),          # CDSHOW  [2]          show/hide CD player widget
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.NUM_3),          # CDPLAY  [3]          play/stop current CD track
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.NUM_4),          # CDPRIOR [4]          previous CD track
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.NUM_5),          # CDNEXT  [5]          next CD track
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.BACK),           # MIRROR  [Backspace]  toggle rear-view mirror
    (IoType.CONTINUOUS, IODevice.JOYSTICK1, JoyInput.POV_AXIS),       # PAN     [Joy POV]    camera pan via joystick hat
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.I),              # OPPPOS  [I]          show opponent positions
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.Y),              # CHAT    [Y]          open multiplayer chat
    # -- group 1: keyboard only — arrows for throttle/brake (InputConfiguration=1) --
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.TAB),            # MAP     [Tab]        toggle minimap on/off
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.Q),              # FMAP    [Q]          switch to fullscreen map
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.E),              # MAPRES  [E]          cycle minimap resolution
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.H),              # HUD     [H]          toggle HUD display
    (IoType.DISCRETE,   IODevice.KEYBOARD,  ScanCode.NUM_8),          # STR     [8]          steer (discrete, key-based)
    (IoType.DISCRETE,   IODevice.KEYBOARD,  ScanCode.LEFT),           # STRL    [← Arrow]    steer left
    (IoType.DISCRETE,   IODevice.KEYBOARD,  ScanCode.RIGHT),          # STRR    [→ Arrow]    steer right
    (IoType.DISCRETE,   IODevice.KEYBOARD,  ScanCode.UP),             # THROT   [↑ Arrow]    throttle
    (IoType.DISCRETE,   IODevice.KEYBOARD,  ScanCode.DOWN),           # BRAKE   [↓ Arrow]    brakes
    (IoType.DISCRETE,   IODevice.KEYBOARD,  ScanCode.SPACE),          # HAND    [Space]      handbrake
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.C),              # CAM     [C]          cycle camera view
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.V),              # XVIEW   [V]          toggle external camera
    (IoType.DISCRETE,   IODevice.KEYBOARD,  ScanCode.RETURN),         # HORN    [Enter]      sound horn
    (IoType.DISCRETE,   IODevice.KEYBOARD,  ScanCode.NUMPAD4),        # LOKL    [Numpad 4]   look left
    (IoType.DISCRETE,   IODevice.KEYBOARD,  ScanCode.NUMPAD6),        # LOKR    [Numpad 6]   look right
    (IoType.DISCRETE,   IODevice.KEYBOARD,  ScanCode.NUMPAD2),        # LOKB    [Numpad 2]   look back
    (IoType.DISCRETE,   IODevice.KEYBOARD,  ScanCode.NUMPAD8),        # LOKF    [Numpad 8]   look forward
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.W),              # WFOV    [W]          toggle wide-angle FOV
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.D),              # DASH    [D]          toggle dashboard view
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.T),              # TRANS   [T]          toggle transmission mode
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.A),              # UPSH    [A]          shift up (manual gearbox)
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.Z),              # DWNS    [Z]          shift down (manual gearbox)
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.R),              # REV     [R]          toggle reverse gear
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.S),              # WYPTN   [S]          next waypoint
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.X),              # WYPTP   [X]          previous waypoint
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.NUM_2),          # CDSHOW  [2]          show/hide CD player widget
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.NUM_3),          # CDPLAY  [3]          play/stop current CD track
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.NUM_4),          # CDPRIOR [4]          previous CD track
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.NUM_5),          # CDNEXT  [5]          next CD track
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.BACK),           # MIRROR  [Backspace]  toggle rear-view mirror
    (IoType.CONTINUOUS, IODevice.JOYSTICK1, JoyInput.POV_AXIS),       # PAN     [Joy POV]    camera pan via joystick hat
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.I),              # OPPPOS  [I]          show opponent positions
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.Y),              # CHAT    [Y]          open multiplayer chat
    # -- group 2: joystick — X-axis steer, Z-axis throttle/brake (InputConfiguration=2) --
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.TAB),            # MAP     [Tab]        toggle minimap on/off
    (IoType.EVENT,      IODevice.JOYSTICK1, JoyInput.BUTTON_5),       # FMAP    [Btn 5]      switch to fullscreen map
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.E),              # MAPRES  [E]          cycle minimap resolution
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.H),              # HUD     [H]          toggle HUD display
    (IoType.CONTINUOUS, IODevice.JOYSTICK1, JoyInput.XAXIS),          # STR     [Joy X]      continuous steering axis
    (IoType.DISCRETE,   IODevice.KEYBOARD,  ScanCode.LEFT),           # STRL    [← Arrow]    steer left (fallback)
    (IoType.DISCRETE,   IODevice.KEYBOARD,  ScanCode.RIGHT),          # STRR    [→ Arrow]    steer right (fallback)
    (IoType.CONTINUOUS, IODevice.JOYSTICK1, JoyInput.ZAXIS_UP),       # THROT   [Joy Z+]     throttle (Z-axis positive)
    (IoType.CONTINUOUS, IODevice.JOYSTICK1, JoyInput.ZAXIS_DOWN),     # BRAKE   [Joy Z-]     brakes (Z-axis negative)
    (IoType.DISCRETE,   IODevice.JOYSTICK1, JoyInput.BUTTON_3),       # HAND    [Btn 3]      handbrake
    (IoType.EVENT,      IODevice.JOYSTICK1, JoyInput.BUTTON_2),       # CAM     [Btn 2]      cycle camera view
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.V),              # XVIEW   [V]          toggle external camera
    (IoType.DISCRETE,   IODevice.JOYSTICK1, JoyInput.BUTTON_9),       # HORN    [Btn 9]      sound horn
    (IoType.DISCRETE,   IODevice.KEYBOARD,  ScanCode.NUMPAD4),        # LOKL    [Numpad 4]   look left
    (IoType.DISCRETE,   IODevice.KEYBOARD,  ScanCode.NUMPAD6),        # LOKR    [Numpad 6]   look right
    (IoType.DISCRETE,   IODevice.KEYBOARD,  ScanCode.NUMPAD2),        # LOKB    [Numpad 2]   look back
    (IoType.DISCRETE,   IODevice.KEYBOARD,  ScanCode.NUMPAD8),        # LOKF    [Numpad 8]   look forward
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.W),              # WFOV    [W]          toggle wide-angle FOV
    (IoType.EVENT,      IODevice.JOYSTICK1, JoyInput.BUTTON_4),       # DASH    [Btn 4]      toggle dashboard view
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.T),              # TRANS   [T]          toggle transmission mode
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.A),              # UPSH    [A]          shift up (manual gearbox)
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.Z),              # DWNS    [Z]          shift down (manual gearbox)
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.R),              # REV     [R]          toggle reverse gear
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.S),              # WYPTN   [S]          next waypoint
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.X),              # WYPTP   [X]          previous waypoint
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.NUM_2),          # CDSHOW  [2]          show/hide CD player widget
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.NUM_3),          # CDPLAY  [3]          play/stop current CD track
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.NUM_4),          # CDPRIOR [4]          previous CD track
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.NUM_5),          # CDNEXT  [5]          next CD track
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.BACK),           # MIRROR  [Backspace]  toggle rear-view mirror
    (IoType.CONTINUOUS, IODevice.JOYSTICK1, JoyInput.POV_AXIS),       # PAN     [Joy POV]    camera pan via joystick hat
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.I),              # OPPPOS  [I]          show opponent positions
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.Y),              # CHAT    [Y]          open multiplayer chat
    # -- group 3: joystick — X-axis steer, buttons throttle/brake (InputConfiguration=3) --
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.TAB),            # MAP     [Tab]        toggle minimap on/off
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.Q),              # FMAP    [Q]          switch to fullscreen map
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.E),              # MAPRES  [E]          cycle minimap resolution
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.H),              # HUD     [H]          toggle HUD display
    (IoType.CONTINUOUS, IODevice.JOYSTICK1, JoyInput.XAXIS),          # STR     [Joy X]      continuous steering axis
    (IoType.DISCRETE,   IODevice.KEYBOARD,  ScanCode.LEFT),           # STRL    [← Arrow]    steer left (fallback)
    (IoType.DISCRETE,   IODevice.KEYBOARD,  ScanCode.RIGHT),          # STRR    [→ Arrow]    steer right (fallback)
    (IoType.DISCRETE,   IODevice.JOYSTICK1, JoyInput.BUTTON_1),       # THROT   [Btn 1]      throttle
    (IoType.DISCRETE,   IODevice.JOYSTICK1, JoyInput.BUTTON_2),       # BRAKE   [Btn 2]      brakes
    (IoType.CONTINUOUS, IODevice.JOYSTICK1, JoyInput.YAXIS_DOWN),     # HAND    [Joy Y-]     handbrake (Y-axis negative)
    (IoType.EVENT,      IODevice.JOYSTICK1, JoyInput.BUTTON_4),       # CAM     [Btn 4]      cycle camera view
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.V),              # XVIEW   [V]          toggle external camera
    (IoType.DISCRETE,   IODevice.JOYSTICK1, JoyInput.BUTTON_3),       # HORN    [Btn 3]      sound horn
    (IoType.DISCRETE,   IODevice.KEYBOARD,  ScanCode.NUMPAD4),        # LOKL    [Numpad 4]   look left
    (IoType.DISCRETE,   IODevice.KEYBOARD,  ScanCode.NUMPAD6),        # LOKR    [Numpad 6]   look right
    (IoType.DISCRETE,   IODevice.KEYBOARD,  ScanCode.NUMPAD2),        # LOKB    [Numpad 2]   look back
    (IoType.DISCRETE,   IODevice.KEYBOARD,  ScanCode.NUMPAD8),        # LOKF    [Numpad 8]   look forward
    (IoType.EVENT,      IODevice.JOYSTICK1, JoyInput.BUTTON_6),       # WFOV    [Btn 6]      toggle wide-angle FOV
    (IoType.EVENT,      IODevice.JOYSTICK1, JoyInput.BUTTON_5),       # DASH    [Btn 5]      toggle dashboard view
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.T),              # TRANS   [T]          toggle transmission mode
    (IoType.EVENT,      IODevice.JOYSTICK1, JoyInput.BUTTON_8),       # UPSH    [Btn 8]      shift up (manual gearbox)
    (IoType.EVENT,      IODevice.JOYSTICK1, JoyInput.BUTTON_7),       # DWNS    [Btn 7]      shift down (manual gearbox)
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.SPACE),          # REV     [Space]      toggle reverse gear
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.S),              # WYPTN   [S]          next waypoint
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.X),              # WYPTP   [X]          previous waypoint
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.NUM_2),          # CDSHOW  [2]          show/hide CD player widget
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.NUM_3),          # CDPLAY  [3]          play/stop current CD track
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.NUM_4),          # CDPRIOR [4]          previous CD track
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.NUM_5),          # CDNEXT  [5]          next CD track
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.BACK),           # MIRROR  [Backspace]  toggle rear-view mirror
    (IoType.CONTINUOUS, IODevice.JOYSTICK1, JoyInput.POV_AXIS),       # PAN     [Joy POV]    camera pan via joystick hat
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.I),              # OPPPOS  [I]          show opponent positions
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.Y),              # CHAT    [Y]          open multiplayer chat
    # -- group 4: joystick — X-axis steer, Y-axis throttle/brake (InputConfiguration=4) --
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.TAB),            # MAP     [Tab]        toggle minimap on/off
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.Q),              # FMAP    [Q]          switch to fullscreen map
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.E),              # MAPRES  [E]          cycle minimap resolution
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.H),              # HUD     [H]          toggle HUD display
    (IoType.CONTINUOUS, IODevice.JOYSTICK1, JoyInput.XAXIS),          # STR     [Joy X]      continuous steering axis
    (IoType.DISCRETE,   IODevice.KEYBOARD,  ScanCode.LEFT),           # STRL    [← Arrow]    steer left (fallback)
    (IoType.DISCRETE,   IODevice.KEYBOARD,  ScanCode.RIGHT),          # STRR    [→ Arrow]    steer right (fallback)
    (IoType.CONTINUOUS, IODevice.JOYSTICK1, JoyInput.YAXIS_UP),       # THROT   [Joy Y+]     throttle (Y-axis positive)
    (IoType.CONTINUOUS, IODevice.JOYSTICK1, JoyInput.YAXIS_DOWN),     # BRAKE   [Joy Y-]     brakes (Y-axis negative)
    (IoType.DISCRETE,   IODevice.KEYBOARD,  ScanCode.SPACE),          # HAND    [Space]      handbrake
    (IoType.EVENT,      IODevice.JOYSTICK1, JoyInput.BUTTON_2),       # CAM     [Btn 2]      cycle camera view
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.V),              # XVIEW   [V]          toggle external camera
    (IoType.DISCRETE,   IODevice.JOYSTICK1, JoyInput.BUTTON_1),       # HORN    [Btn 1]      sound horn
    (IoType.DISCRETE,   IODevice.KEYBOARD,  ScanCode.NUMPAD4),        # LOKL    [Numpad 4]   look left
    (IoType.DISCRETE,   IODevice.KEYBOARD,  ScanCode.NUMPAD6),        # LOKR    [Numpad 6]   look right
    (IoType.DISCRETE,   IODevice.KEYBOARD,  ScanCode.NUMPAD2),        # LOKB    [Numpad 2]   look back
    (IoType.DISCRETE,   IODevice.KEYBOARD,  ScanCode.NUMPAD8),        # LOKF    [Numpad 8]   look forward
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.W),              # WFOV    [W]          toggle wide-angle FOV
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.D),              # DASH    [D]          toggle dashboard view
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.T),              # TRANS   [T]          toggle transmission mode
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.A),              # UPSH    [A]          shift up (manual gearbox)
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.Z),              # DWNS    [Z]          shift down (manual gearbox)
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.R),              # REV     [R]          toggle reverse gear
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.S),              # WYPTN   [S]          next waypoint
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.X),              # WYPTP   [X]          previous waypoint
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.NUM_2),          # CDSHOW  [2]          show/hide CD player widget
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.NUM_3),          # CDPLAY  [3]          play/stop current CD track
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.NUM_4),          # CDPRIOR [4]          previous CD track
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.NUM_5),          # CDNEXT  [5]          next CD track
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.BACK),           # MIRROR  [Backspace]  toggle rear-view mirror
    (IoType.CONTINUOUS, IODevice.JOYSTICK1, JoyInput.POV_AXIS),       # PAN     [Joy POV]    camera pan via joystick hat
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.I),              # OPPPOS  [I]          show opponent positions
    (IoType.EVENT,      IODevice.KEYBOARD,  ScanCode.Y),              # CHAT    [Y]          open multiplayer chat
]

def make_default_io_devs() -> List["IODev"]:
    """Return the 165 game-default IODev bindings as IODev objects."""
    return [IODev(io_type=t, device=d, component=c) for t, d, c in _DEFAULT_IO_DEVS]


@dataclass
class AudioConfig:
    wav_vol:     float = 1.0
    cd_vol:      float = 1.0
    balance:     float = 0.0
    flags:       int   = 0
    channels:    int   = 16
    device_name: str   = ""

    @property
    def sfx(self)         -> bool: return bool(self.flags & 1)
    @property
    def cd_music(self)    -> bool: return bool(self.flags & 2)
    @property
    def hi_res(self)      -> bool: return bool(self.flags & 4)
    @property
    def stereo(self)      -> bool: return bool(self.flags & 8)
    @property
    def hi_sample(self)   -> bool: return bool(self.flags & 16)
    @property
    def commentary(self)  -> bool: return bool(self.flags & 32)


@dataclass
class GfxConfig:
    tex:           int   = Quality.HIGH
    obj:           int   = Quality.HIGH
    shadows:       int   = Shadows.VEHICLES
    env_map:       int   = ON
    sphr_map:      int   = ON
    sky:           int   = ON
    far_clip:      float = 500.0
    light_quality: float = 1.0
    particles:     float = 1.0
    disable_peds:  int   = OFF
    interlaced:    int   = OFF
    speed_loading: int   = OFF
    tex_filter:    int   = ON


@dataclass
class IODev:
    io_type:   int = 0
    device:    int = 0
    component: int = 0


@dataclass
class CtrlConfig:
    input_type:   int   = InputType.MOUSE
    transmission: int   = Transmission.AUTO
    physics_real: float = 0.0
    auto_reverse: int   = ON
    use_pov_hat:  int   = OFF
    use_force_fb: int   = OFF
    ff_scale:     float = 1.0
    road_force:   float = 1.0
    mouse_sens:   float = 1.0
    joy_dead_zone:float = 0.1
    steer_delta:  float = 0.05
    steer_limit:  float = 1.0
    steer_sens:   float = 1.0
    io_devs: List[IODev] = field(default_factory=make_default_io_devs)


@dataclass
class ViewConfig:
    camera_index:   int = Camera.HOOD
    hudmap_mode:    int = HudMap.NONE
    wide_view:      int = OFF
    dash_view:      int = OFF
    enable_mirror:  int = OFF
    external_view:  int = OFF
    xcam_view:      int = OFF
    icons_state:    int = ON
    map_res:        int = 2


@dataclass
class PlayerConfig:
    type_:    int = 1234
    version:  int = 18
    audio:    AudioConfig = field(default_factory=AudioConfig)
    gfx:      GfxConfig   = field(default_factory=GfxConfig)
    ctrl:     CtrlConfig  = field(default_factory=CtrlConfig)
    view:     ViewConfig  = field(default_factory=ViewConfig)

    def write(self, path: Path) -> None:
        a = self.audio
        g = self.gfx
        c = self.ctrl
        v = self.view

        with open(path, "wb") as f:
            write_pack(f, "<ii", self.type_, self.version)  # Header

            # Audio
            write_pack(f, "<fff", a.wav_vol, a.cd_vol, a.balance)
            write_pack(f, "<II",  a.flags, a.channels)
            name_bytes = a.device_name.encode(Encoding.ASCII, "replace") + b"\x00"
            write_pack(f, "<i", len(name_bytes))
            f.write(name_bytes)

            # Gfx (6 x u32 + 3 x f32 + 4 x u32 = 13 fields)
            write_pack(f, "<IIIIII", g.tex, g.obj, g.shadows, g.env_map, g.sphr_map, g.sky)
            write_pack(f, "<fff",    g.far_clip, g.light_quality, g.particles)
            write_pack(f, "<IIII",   g.disable_peds, g.interlaced, g.speed_loading, g.tex_filter)

            # Ctrl scalars (i32 + u32/f32 mix = 13 fields)
            write_pack(f, "<i",       c.input_type)
            write_pack(f, "<I",       c.transmission)
            write_pack(f, "<f",       c.physics_real)
            write_pack(f, "<II",      c.auto_reverse, c.use_pov_hat)
            write_pack(f, "<I",       c.use_force_fb)
            write_pack(f, "<fffffff", c.ff_scale, c.road_force, c.mouse_sens, c.joy_dead_zone, c.steer_delta, c.steer_limit, c.steer_sens)

            # IODevs (165 x 12 bytes)
            devs = c.io_devs
            if len(devs) != NUM_IODEV_SLOTS:
                raise ValueError(f"Expected {NUM_IODEV_SLOTS} IODev slots, got {len(devs)}")
            for d in devs:
                write_pack(f, "<iii", d.io_type, d.device, d.component)

            # View (9 x i8 + 1 pad)
            write_pack(f, "<10b",
                v.camera_index, v.hudmap_mode, v.wide_view, v.dash_view,
                v.enable_mirror, v.external_view, v.xcam_view, v.icons_state,
                v.map_res, 0)

    @classmethod
    def read(cls, path: Path) -> "PlayerConfig":
        buf = io.BytesIO(path.read_bytes())

        def ri(): return read_unpack(buf, "<i")[0]
        def ru(): return read_unpack(buf, "<I")[0]
        def rf(): return read_unpack(buf, "<f")[0]
        def rb(): return read_unpack(buf, "<b")[0]

        type_   = ri()
        version = ri()

        audio = AudioConfig(
            wav_vol     = rf(),
            cd_vol      = rf(),
            balance     = rf(),
            flags       = ru(),
            channels    = ru(),
        )
        nlen = ri()
        audio.device_name = read_binary_name(buf, nlen)

        gfx = GfxConfig(
            tex           = ru(),
            obj           = ru(),
            shadows       = ru(),
            env_map       = ru(),
            sphr_map      = ru(),
            sky           = ru(),
            far_clip      = rf(),
            light_quality = rf(),
            particles     = rf(),
            disable_peds  = ru(),
            interlaced    = ru(),
            speed_loading = ru(),
            tex_filter    = ru(),
        )

        ctrl = CtrlConfig(
            input_type    = ri(),
            transmission  = ru(),
            physics_real  = rf(),
            auto_reverse  = ru(),
            use_pov_hat   = ru(),
            use_force_fb  = ru(),
            ff_scale      = rf(),
            road_force    = rf(),
            mouse_sens    = rf(),
            joy_dead_zone = rf(),
            steer_delta   = rf(),
            steer_limit   = rf(),
            steer_sens    = rf(),
            io_devs       = [IODev(ri(), ri(), ri()) for _ in range(NUM_IODEV_SLOTS)],
        )

        view = ViewConfig(
            camera_index  = rb(),
            hudmap_mode   = rb(),
            wide_view     = rb(),
            dash_view     = rb(),
            enable_mirror = rb(),
            external_view = rb(),
            xcam_view     = rb(),
            icons_state   = rb(),
            map_res       = rb(),
        )
        rb()  # trailing pad byte

        pos  = buf.tell()
        size = len(buf.getvalue())
        if pos != size:
            raise ValueError(f"PlayerConfig size mismatch: consumed {pos} of {size} bytes")

        return cls(type_=type_, version=version, audio=audio, gfx=gfx, ctrl=ctrl, view=view)
    
    def to_text(self, file_size: Optional[int] = None) -> str:
        lines: List[str] = []
        w = lambda s="": lines.append(s + "\n")

        a = self.audio
        g = self.gfx
        c = self.ctrl
        v = self.view

        if file_size is not None:
            w(f"  file_size    : {file_size} bytes  (expected 2147)")
        w(f"\tType         : {self.type_}  (mmInfoBase::Type = 1234)")
        w(f"\tVersion      : {self.version}  (kPlayerConfigVersion = 18)")

        w()
        w("  -- Audio  (mmAudioCFG) --")
        w(f"\tWavVol       : {a.wav_vol:.6f}  (SFX/wave volume 0.0-1.0)")
        w(f"\tCDVol        : {a.cd_vol:.6f}  (music/CD volume 0.0-1.0)")
        w(f"\tBalance      : {a.balance:+.6f}  (L/R pan: -1=full left, 0=centre, +1=full right)")
        w(f"\tFlags        : {a.flags:#010x} = {a.flags:032b}b")
        w(f"\t             :   bit0 SFX={a.sfx}  bit1 CDMusic={a.cd_music}  bit2 HiRes={a.hi_res}")
        w(f"\t             :   bit3 Stereo={a.stereo}  bit4 HiSample={a.hi_sample}  bit5 Commentary={a.commentary}")
        w(f"\tChannels     : {a.channels}  (max simultaneous audio channels)")
        w(f"\tDeviceName   : {a.device_name!r}  (DirectSound device)")

        w()
        w("  -- Graphics  (mmGfxCFG -- 52 bytes, 13 fields) --")
        w(f"\tTex          : {g.tex}  (texture quality   0=low .. 3=very high)")
        w(f"\tObj          : {g.obj}  (object detail     0=low .. 3=very high)")
        w(f"\tShadows      : {g.shadows}  (0=off, 1=vehicles, 2=+props, 3=+skidmarks)")
        w(f"\tEnvMap       : {g.env_map}  (vehicle reflections  0=off 1=on)")
        w(f"\tSphrMap      : {g.sphr_map}  (sphere/specular map  0=off 1=on)")
        w(f"\tSky          : {g.sky}  (textured sky         0=off 1=on)")
        w(f"\tFarClip      : {g.far_clip:.2f}  (far clip distance in game units)")
        w(f"\tLightQuality : {g.light_quality:.4f}  (lighting quality slider)")
        w(f"\tParticles    : {g.particles:.4f}  (particle density)")
        w(f"\tDisablePeds  : {g.disable_peds}  (0=visible, 1=hidden)")
        w(f"\tInterlaced   : {g.interlaced}")
        w(f"\tSpeedLoading : {g.speed_loading}")
        w(f"\tTexFilter    : {g.tex_filter}  (0=off 1=on)")

        w()
        w("  -- Controls  (mmCtrlCFG -- 13 scalars + 165 IODev slots) --")
        w(f"\tInputType    : {c.input_type}  ({InputType.NAMES.get(c.input_type, c.input_type)})")
        w(f"\tTransmission : {c.transmission}  ({'Auto' if c.transmission else 'Manual'})")
        w(f"\tPhysicsReal  : {c.physics_real:.6f}  (collision intensity  0.0=arcade, 1.0=sim)")
        w(f"\tAutoReverse  : {c.auto_reverse}  ({bool(c.auto_reverse)})")
        w(f"\tUsePOVHat    : {c.use_pov_hat}  (joystick POV hat)")
        w(f"\tUseForceFB   : {c.use_force_fb}  (force feedback)")
        w(f"\tFFScale      : {c.ff_scale:.6f}  (force feedback scale)")
        w(f"\tRoadForce    : {c.road_force:.6f}  (road force scale)")
        w(f"\tMouseSens    : {c.mouse_sens:.6f}  (mouse sensitivity)")
        w(f"\tJoyDeadZone  : {c.joy_dead_zone:.6f}  (joystick dead zone)")
        w(f"\tSteerDelta   : {c.steer_delta:.6f}  (discrete steering delta)")
        w(f"\tSteerLimit   : {c.steer_limit:.6f}  (discrete steering limit)")
        w(f"\tSteerSens    : {c.steer_sens:.6f}  (user steering sensitivity)")

        bound = [(i, d) for i, d in enumerate(c.io_devs) if d.io_type or d.device or d.component]
        w()
        w(f"  IODev bindings : {len(bound)}/165 slots non-zero")
        w(f"  (each slot = IoType[i32] + Device[i32] + Component[i32] = 12 bytes)")
        if bound:
            w(f"  {'slot':>4}  {'IoType':>7}  {'Device':>7}  {'Component':>10}")
            w(f"  {'----':>4}  {'-------':>7}  {'-------':>7}  {'----------':>10}")
            for i, d in bound:
                w(f"  [{i:3d}]  {d.io_type:7d}  {d.device:7d}  {d.component:10d}")

        w()
        w("  -- View settings  (mmViewCFG -- 10 bytes) --")
        w(f"\tCameraIndex  : {v.camera_index}  ({Camera.NAMES.get(v.camera_index, v.camera_index)})")
        w(f"\tHudmapMode   : {v.hudmap_mode}  (minimap mode)")
        w(f"\tWideView     : {v.wide_view}  ({bool(v.wide_view)})")
        w(f"\tDashView     : {v.dash_view}  ({bool(v.dash_view)})")
        w(f"\tEnableMirror : {v.enable_mirror}  ({bool(v.enable_mirror)})")
        w(f"\tExternalView : {v.external_view}  ({bool(v.external_view)})")
        w(f"\tXcamView     : {v.xcam_view}  ({bool(v.xcam_view)})")
        w(f"\tIconsState   : {v.icons_state}  ({bool(v.icons_state)})")
        w(f"\tMapRes       : {v.map_res}  (minimap resolution)")

        return "".join(lines)

    @classmethod
    def debug_file(cls, input_file: Path, output_file: Path, enabled: bool) -> None:
        if not enabled:
            return
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        cfg = cls.read(input_file)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(cfg.to_text(file_size=input_file.stat().st_size))
            
        print(f"  Debugged {input_file.name} -> {output_file.name}")