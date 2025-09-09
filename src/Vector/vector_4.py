from src.IO.binary import calc_size


class Vector4:
    def __init__(self, x: float, y: float, z: float, w: float) -> None:
        self.x = x
        self.y = y
        self.z = z
        self.w = w
        
    @staticmethod
    def binary_size() -> int:
        return calc_size('4f') 