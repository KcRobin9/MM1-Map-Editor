from typing import BinaryIO

from src.io.binary import read_unpack
from src.core.vector.vector_3 import Vector3


class aiIntersection:
    def load(self, f: BinaryIO) -> None:
        self.id, = read_unpack(f, '<H')
        self.position = Vector3.read(f, '<')

        num_sinks, = read_unpack(f, '<H')
        self.sinks = read_unpack(f, f'<{num_sinks}I')

        num_sources, = read_unpack(f, '<H')
        self.sources = read_unpack(f, f'<{num_sources}I')

        self.paths = read_unpack(f, f'<{num_sinks + num_sources}I')
        self.directions = read_unpack(f, f'<{num_sinks + num_sources}f')

    @staticmethod
    def read(f: BinaryIO) -> 'aiIntersection':
        result = aiIntersection()
        result.load(f)
        return result