from src.constants.vehicles import PlayerCar
from src.constants.modes import GameMode, Difficulty
from src.file_formats.player_profile import PlayerData, PlayerRecord
from src.constants.constants import ON, OFF
from src.constants.menu import (
    Quality, Shadows, Camera, InputType, Transmission,
    HudMap, AudioFlags, Progress,
)
from src.file_formats.player_config import (
    PlayerConfig, 
    AudioConfig, GfxConfig, CtrlConfig, ViewConfig,
    make_default_io_devs,
)


NAME = "Robin"  # sets both player_name and net_name

auto_select_profile = True   # True = players.dir auto-selects this profile on boot


my_profile = PlayerData(

    player_name = NAME,
    net_name    = NAME,
    file_name   = "player0",    # .sav / .cfg basename

    difficulty  = Difficulty.PROFESSIONAL,
    progress    = Progress.ALL,  # all 12 races unlocked

    last_car_picked  = PlayerCar.PANOZ_GTR1,
    last_car_color   = 3,        # 0-based paint index
    last_game_picked = GameMode.CHECKPOINT,
    last_race_picked = 0,

    checkpoint_records = [
        # time(s)   car                         score  passed
        PlayerRecord( 11.00, PlayerCar.MUSTANG_GT,   450, 1),  # [0]
        PlayerRecord( 14.00, PlayerCar.MUSTANG_GT,   450, 1),  # [1]
        PlayerRecord( 17.00, PlayerCar.MUSTANG_GT,   450, 1),  # [2]
        PlayerRecord( 20.00, PlayerCar.CADILLAC,     750, 1),  # [3]
        PlayerRecord( 23.00, PlayerCar.CADILLAC,     750, 1),  # [4]
        PlayerRecord( 26.00, PlayerCar.CADILLAC,     750, 1),  # [5]
        PlayerRecord( 29.00, PlayerCar.POLICE,       375, 1),  # [6]
        PlayerRecord( 32.00, PlayerCar.POLICE,       375, 1),  # [7]
        PlayerRecord( 35.00, PlayerCar.FORD_F350,    375, 1),  # [8]
        PlayerRecord( 38.00, PlayerCar.ROADSTER,     200, 1),  # [9]
        PlayerRecord( 41.00, PlayerCar.ROADSTER,     200, 1),  # [10]
        PlayerRecord( 44.00, PlayerCar.PANOZ_GTR1,   200, 1),  # [11]
    ],

    circuit_records = [
        # time(s)   car                         score  passed
        PlayerRecord( 11.00, PlayerCar.CADILLAC,     400, 1),  # [0]
        PlayerRecord( 14.00, PlayerCar.CADILLAC,     400, 1),  # [1]
        PlayerRecord( 17.00, PlayerCar.CADILLAC,     400, 1),  # [2]
        PlayerRecord( 20.00, PlayerCar.CADILLAC,     400, 1),  # [3]
        PlayerRecord( 23.00, PlayerCar.MUSTANG_GT,   450, 1),  # [4]
        PlayerRecord( 26.00, PlayerCar.MUSTANG_GT,   450, 1),  # [5]
        PlayerRecord( 29.00, PlayerCar.MUSTANG_GT,   450, 1),  # [6]
        PlayerRecord( 32.00, PlayerCar.ROADSTER,     500, 1),  # [7]
        PlayerRecord( 35.00, PlayerCar.ROADSTER,     500, 1),  # [8]
        PlayerRecord( 38.00, PlayerCar.PANOZ_GTR1,   600, 1),  # [9]
        PlayerRecord( 41.00, PlayerCar.PANOZ_GTR1,   600, 1),  # [10]
        PlayerRecord( 44.00, PlayerCar.PANOZ_GTR1,   600, 1),  # [11]
    ],

    blitz_records = [
        # time(s)   car                         score  passed
        PlayerRecord( 11.00, PlayerCar.MUSTANG_GT,   450, 1),  # [0]
        PlayerRecord( 14.00, PlayerCar.MUSTANG_GT,   450, 1),  # [1]
        PlayerRecord( 17.00, PlayerCar.MUSTANG_GT,   450, 1),  # [2]
        PlayerRecord( 20.00, PlayerCar.POLICE,       350, 1),  # [3]
        PlayerRecord( 23.00, PlayerCar.POLICE,       350, 1),  # [4]
        PlayerRecord( 26.00, PlayerCar.FASTBACK,     500, 1),  # [5]
        PlayerRecord( 29.00, PlayerCar.FASTBACK,     500, 1),  # [6]
        PlayerRecord( 32.00, PlayerCar.ROADSTER,     500, 1),  # [7]
        PlayerRecord( 35.00, PlayerCar.ROADSTER,     500, 1),  # [8]
        PlayerRecord( 38.00, PlayerCar.PANOZ_GTR1,   600, 1),  # [9]
        PlayerRecord( 41.00, PlayerCar.PANOZ_GTR1,   600, 1),  # [10]
        PlayerRecord( 44.00, PlayerCar.PANOZ_GTR1,   600, 1),  # [11]
    ],
)


# Set to None to leave the existing .cfg untouched.
my_config = PlayerConfig(

    audio = AudioConfig(
        wav_vol     = 0.8,          # 0.0-1.0
        cd_vol      = 0.7,          # 0.0-1.0
        balance     = 0.0,
        flags       = AudioFlags.DEFAULT,   # SFX | CD_MUSIC | HI_RES | COMMENTARY
        channels    = 32,
        device_name = "Primary Sound Driver",
    ),

    gfx = GfxConfig(
        tex           = Quality.VERY_HIGH,
        obj           = Quality.VERY_HIGH,
        shadows       = Shadows.SKIDMARKS,
        env_map       = ON,
        sphr_map      = ON,
        sky           = ON,
        far_clip      = 1000.0,     # game units
        light_quality = 3.0,
        particles     = 1.0,
        disable_peds  = OFF,
        interlaced    = OFF,
        speed_loading = OFF,
        tex_filter    = ON,
    ),

    ctrl = CtrlConfig(
        input_type    = InputType.MOUSE,
        transmission  = Transmission.AUTO,
        physics_real  = 0.0,        # 0.0=arcade  1.0=sim
        auto_reverse  = ON,
        use_pov_hat   = OFF,
        use_force_fb  = OFF,
        ff_scale      = 1.0,
        road_force    = 1.0,
        mouse_sens    = 1.0,
        joy_dead_zone = 0.1,
        steer_delta   = 0.0,
        steer_limit   = 1.0,
        steer_sens    = 1.0,
        io_devs       = make_default_io_devs(),
    ),

    view = ViewConfig(
        camera_index  = Camera.FAR,
        hudmap_mode   = HudMap.SMALL,
        wide_view     = OFF,
        dash_view     = OFF,
        enable_mirror = ON,
        external_view = ON,
        xcam_view     = OFF,
        icons_state   = ON,
        map_res       = 1,
    ),
)


extra_profiles = [
    # PlayerData(player_name="Tester", file_name="player1", progress=0x007),
]

extra_configs = []
