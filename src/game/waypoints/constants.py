WAYPOINT_FILLER = ",0,0,0,0,0,\n"


class Rotation:
    AUTO = 0
    NORTH = 0.01
    NORTH_EAST = 45
    EAST = 90
    SOUTH_EAST = 135
    SOUTH = 179.99
    SOUTH_WEST = -135
    WEST = -90
    NORTH_WEST = -45
    AUTO = 0
    
    FULL_CIRCLE = 360
    HALF_CIRCLE = 180
    
    
class Width:
    AUTO = 0
    DEFAULT = 15
    ALLEY = 3
    SMALL = 11
    MEDIUM = 15
    LARGE = 19