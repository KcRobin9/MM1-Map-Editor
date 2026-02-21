from typing import Tuple


class Color:
    RED = "#ff0000"
    RED_LIGHT = "#ff8080"
    RED_DARK = "#800000"
    
    GREEN = "#00ff00"
    GREEN_LIGHT = "#80ff80"
    GREEN_DARK = "#008000"
    
    BLUE = "#0000ff"
    BLUE_LIGHT = "#8080ff"
    BLUE_DARK = "#000080"  # Dading: #070644
    
    PURPLE = "#800080"
    PURPLE_LIGHT = "#c080c0"
    PURPLE_DARK = "#400040"
    
    YELLOW = "#ffff00"
    YELLOW_LIGHT = "#ffff80"
    YELLOW_DARK = "#808000"
    
    GOLD = "#ffd700"
    GOLD_LIGHT = "#ffeb80"
    GOLD_DARK = "#806b00"
    
    WHITE = "#ffffff"
    WHITE_DARK = "#cccccc"  # Light gray

    ORANGE = "#ffa500"

    WOOD = "#7b5931"
    SNOW = "#cdcecd"
    WATER = "#5d8096"
    ROAD = "#414441"
    GRASS = "#396d18"

    IND_WALL = "#7b816a"
    BRICKS_MALL = "#e6cab4"
    SHOP_BRICK = "#394441"
    MARKT_BRICK = "#9c9183"

    @staticmethod
    def to_rgba(hex_color: str, alpha: float = 1.0) -> Tuple[float, float, float, float]:
        hex_color = hex_color.lstrip("#")
        r, g, b = (int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))
        return (r, g, b, alpha)