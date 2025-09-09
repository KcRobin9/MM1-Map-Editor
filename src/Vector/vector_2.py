from typing import List, Tuple, BinaryIO
from src.IO.binary import read_unpack, write_pack, calc_size


class Vector2:
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y
            
    @staticmethod
    def read(file: BinaryIO, byte_order: str = '<') -> 'Vector2':
        return Vector2(*read_unpack(file, f'{byte_order}2f'))

    @staticmethod
    def readn(file: BinaryIO, count: int, byte_order: str = '<') -> List['Vector2']:
        return [Vector2.read(file, byte_order) for _ in range(count)]
            
    def write(self, file: BinaryIO, byte_order: str = '<') -> None:
        write_pack(file, f'{byte_order}2f', self.x, self.y)
        
    @staticmethod
    def binary_size() -> int:
        return calc_size('2f')
                
    def __add__(self, other: 'Vector2') -> 'Vector2':
        return Vector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: 'Vector2') -> 'Vector2':
        return Vector2(self.x - other.x, self.y - other.y)

    def __mul__(self, other: float) -> 'Vector2':
        return Vector2(self.x * other, self.y * other)

    def __truediv__(self, other: float) -> 'Vector2':
        return Vector2(self.x / other, self.y / other)

    def __eq__(self, other: 'Vector2') -> bool:
        return (self.x, self.y) == (other.x, other.y)

    def __hash__(self) -> int:
        return hash((self.x, self.y))

    def tuple(self) -> Tuple[float, float]:
        return (self.x, self.y)

    def Cross(self, rhs: 'Vector2' = None) -> 'Vector2':
        if rhs is None:
            return Vector2(self.y, -self.x)

        return Vector2((self.x*rhs.y) - (self.y*rhs.x))

    def Dot(self, rhs: 'Vector2') -> float:
        return (self.x * rhs.x) + (self.y * rhs.y)

    def Mag2(self) -> float:
        return (self.x * self.x) + (self.y * self.y)

    def Dist2(self, other: 'Vector2') -> float:
        return (other - self).Mag2()

    def Dist(self, other: 'Vector2') -> float:
        return self.Dist2(other) ** 0.5
    
    def Normalize(self) -> 'Vector2':
        return self * (self.Mag2() ** -0.5)
    
    def __repr__(self) -> str:
        return f'{round(self.x, 2):.2f}, {round(self.y, 2):.2f}'