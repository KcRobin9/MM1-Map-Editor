from src.IO.binary_parsing import read_unpack, write_pack, calc_size
from typing import List, Tuple, BinaryIO
import math


class Vector3:
    def __init__(self, x: float, y: float, z: float) -> None:
        self.x = x
        self.y = y
        self.z = z
        self._data = {"x": x, "y": y, "z": z}
        
    @staticmethod
    def read(file: BinaryIO, byte_order: str = '<') -> 'Vector3':
        return Vector3(*read_unpack(file, f'{byte_order}3f'))

    @staticmethod
    def readn(file: BinaryIO, count: int, byte_order: str = '<') -> List['Vector3']:
        return [Vector3.read(file, byte_order) for _ in range(count)]
    
    def write(self, file: BinaryIO, byte_order: str = '<') -> None:
        write_pack(file, f'{byte_order}3f', self.x, self.y, self.z)
        
    @staticmethod
    def binary_size() -> int:
        return calc_size('3f')
        
    @classmethod
    def from_tuple(cls, vertex_tuple: Tuple[float, float, float]) -> 'Vector3':
        return cls(*vertex_tuple)

    def to_tuple(self) -> Tuple[float, float, float]:
        return (self.x, self.y, self.z)
        
    def copy(self) -> 'Vector3':
        return Vector3(self.x, self.y, self.z)
    
    def __getitem__(self, key: str) -> float:
        return self._data[key]

    def __setitem__(self, key: str, value: float) -> None:
        if key in self._data:
            self._data[key] = value
            setattr(self, key, value)
        else:
            raise ValueError(f"Invalid key: {key}. Use 'x', 'y', or 'z'.")

    def __add__(self, other: 'Vector3') -> 'Vector3':
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: 'Vector3') -> 'Vector3':
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, other: float) -> 'Vector3':
        return Vector3(self.x * other, self.y * other, self.z * other)

    def __truediv__(self, other: float) -> 'Vector3':
        return Vector3(self.x / other, self.y / other, self.z / other)

    def __eq__(self, other: 'Vector3') -> bool:
        return (self.x, self.y, self.z) == (other.x, other.y, other.z)

    def __hash__(self) -> int:
        return hash((self.x, self.y, self.z))
    
    def Cross(self, rhs: 'Vector3') -> 'Vector3':
        return Vector3(self.y * rhs.z - self.z * rhs.y, self.z * rhs.x - self.x * rhs.z, self.x * rhs.y - self.y * rhs.x)

    def Dot(self, rhs: 'Vector3') -> float:
        return (self.x * rhs.x) + (self.y * rhs.y) + (self.z * rhs.z)
    
    def Mag(self) -> float:
        return self.Mag2() ** 0.5
    
    def Mag2(self) -> float:
        return (self.x * self.x) + (self.y * self.y) + (self.z * self.z)

    def Normalize(self) -> 'Vector3':
        return self * (self.Mag2() ** -0.5)

    def Dist2(self, other: 'Vector3') -> float:
        return (other - self).Mag2()

    def Dist(self, other: 'Vector3') -> float:
        return self.Dist2(other) ** 0.5
        
    def Angle(self, rhs: 'Vector3') -> float:
        return math.acos(self.Dot(rhs) * ((self.Mag2() * rhs.Mag2()) ** -0.5))
    
    def Negate(self) -> 'Vector3':
        return Vector3(-self.x, -self.y, -self.z)

    def Set(self, x: float, y: float, z: float) -> None:
        self.x = x
        self.y = y
        self.z = z
                
    def __repr__(self) -> str:
        return f'{{ {round(self.x, 2):.2f}, {round(self.y, 2):.2f}, {round(self.z, 2):.2f} }}'