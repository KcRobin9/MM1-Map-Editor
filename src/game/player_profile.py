from src.constants.folder import Folder
from src.file_formats.player_profile import write_player_profile

try:
    import src.USER.player_profile as _up
except ImportError:
    _up = None


def apply_player_profile() -> None:
    """Write .sav + .cfg + players.dir into the MM install from the user config.
    Safe no-op if the user module is not importable."""
    if _up is None:
        print(f"\tSkipping player profile -- {Folder.Src.User.PlayerProfile} not loadable")
        return

    write_player_profile(
        output_folder       = Folder.MidtownMadness.DevPlayers,
        profile             = _up.my_profile,
        config              = getattr(_up, "my_config",      None),
        make_default        = _up.auto_select_profile,
        additional_profiles = getattr(_up, "extra_profiles", []) or None,
        additional_configs  = getattr(_up, "extra_configs",  []) or None,
    )
