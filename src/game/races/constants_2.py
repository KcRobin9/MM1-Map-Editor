from src.constants.misc import Folder
from src.constants.modes import RaceMode
from src.constants.file_formats import FileType


class IntersectionType:
    STOP = 0
    STOP_LIGHT = 1
    YIELD = 2
    CONTINUE = 3


class CopsAndRobbers:
    BANK_HIDEOUT = "Bank Hideout"
    GOLD_POSITION = "Gold Position"
    ROBBER_HIDEOUT = "Robber Hideout"


class CopBehavior:
    FOLLOW = 0x1      # Follow, only following the player
    ROADBLOCK = 0x2   # Attempt to create roadblocks
    SPINOUT = 0x4     # Try to spin the player out
    PUSH = 0x8        # Pushing behavior, ramming from the back

    MIX = FOLLOW | ROADBLOCK | SPINOUT | PUSH     # Mix of all behaviors

    FOLLOW_AND_SPINOUT = FOLLOW | SPINOUT         # Follow and try to spin out
    FOLLOW_AND_PUSH = FOLLOW | PUSH               # Follow and push
    ROADBLOCK_AND_SPINOUT = ROADBLOCK | SPINOUT   # Attempt roadblocks and spin out
    ROADBLOCK_AND_PUSH = ROADBLOCK | PUSH         # Attempt roadblocks and push
    SPINOUT_AND_PUSH = SPINOUT | PUSH             # Spin out and push
    
    AGGRESSIVE = ROADBLOCK | SPINOUT | PUSH       # All behaviors except follow
    DEFENSIVE = FOLLOW | ROADBLOCK                # More passive, keeping distance
    CUNNING = FOLLOW | SPINOUT                    # Following and occasionally spinning out
    PERSISTENT = FOLLOW | PUSH                    # Persistently following and pushing
    UNPREDICTABLE = ROADBLOCK | FOLLOW | SPINOUT  # Unpredictable mix of behaviors
    

class CopDensity:
    _0 = 0.0
    _100 = 1.0  # The game only supports 0.0 and 1.0
    
    
class CopStartLane:
    STATIONARY = 0 
    PED = 1  # Broken, do not use (this feature was never finished by the game's developers)
    IN_TRAFFIC = 2    
    
    
class Density:
    _0 = 0.0
    _10 = 0.1
    _20 = 0.2
    _30 = 0.3
    _40 = 0.4
    _50 = 0.5
    _60 = 0.6
    _70 = 0.7
    _80 = 0.8
    _90 = 0.9
    _100 = 1.0


class PedDensity(Density):
    pass
    
    
class AmbientDensity(Density):
    pass


class NumericOptions:
    _0 = 0
    _1 = 1
    _2 = 2
    _3 = 3
    _4 = 4
    _5 = 5
    _6 = 6
    _7 = 7
    _8 = 8

class MaxOpponents(NumericOptions):
    # The game can (likely) support more than 128 opponents, however the game's "MAX_MOVERS" is capped at 128
    # (see: Open1560 / code / midtown / mmphysics / phys.cpp)
    _128 = 128  


class Laps(NumericOptions):
     # The game can load races with 1000+ laps, however the game's menu caps the number to 10
    _9 = 9
    _10 = 10


MM_DATA_FILES  = {
        RaceMode.CHECKPOINT: Folder.SHOP_RACE_MAP / f"MM{RaceMode.CHECKPOINT}DATA{FileType.CSV}",
        RaceMode.CIRCUIT: Folder.SHOP_RACE_MAP / f"MM{RaceMode.CIRCUIT}DATA{FileType.CSV}",
        RaceMode.BLITZ: Folder.SHOP_RACE_MAP / f"MM{RaceMode.BLITZ}DATA{FileType.CSV}"
}