from typing import BinaryIO

from src.core.vector.vector_3 import Vector3
from src.io.binary import read_unpack, read_binary_name


class aiStreet:                  
    def load(self, f: BinaryIO) -> None:
        self.id, = read_unpack(f, '<H')
        self.num_vertexes, = read_unpack(f, '<H')
        self.num_lanes, = read_unpack(f, '<H')
        self.num_sidewalks, = read_unpack(f, '<H')
        self.stop_light_index, = read_unpack(f, '<H')
        self.intersection_type, = read_unpack(f, '<H')
        self.blocked, = read_unpack(f, '<H')
        self.ped_blocked, = read_unpack(f, '<H')
        self.divided, = read_unpack(f, '<H')
        self.is_flat, = read_unpack(f, '<H')
        self.has_bridge, = read_unpack(f, '<H')
        self.alley, = read_unpack(f, '<H')
        self.road_length, = read_unpack(f, '<f')
        self.speed_limit, = read_unpack(f, '<f')
        self.stop_light_name = read_binary_name(f, 32)
        self.oncoming_path, = read_unpack(f, '<I')
        self.edge_index, = read_unpack(f, '<I')
        self.path_index, = read_unpack(f, '<I')
        self.sub_section_offsets = read_unpack(f, f'<{self.num_vertexes * (self.num_lanes + self.num_sidewalks)}f')
        self.center_offsets = read_unpack(f, f'<{self.num_vertexes}f')
        self.intersection_ids = read_unpack(f, '<2I')
        self.lane_vertices = Vector3.readn(f, self.num_vertexes * (self.num_lanes + self.num_sidewalks))

        # Center / Dividing line between the two sides of the road
        self.center_vertices = Vector3.readn(f, self.num_vertexes)
        self.vert_x_dirs = Vector3.readn(f, self.num_vertexes)
        self.normals = Vector3.readn(f, self.num_vertexes)
        self.vert_z_dirs = Vector3.readn(f, self.num_vertexes)
        self.sub_section_dirs = Vector3.readn(f, self.num_vertexes)

        # Outer Edges, Inner Edges (Curb)
        self.boundaries = Vector3.readn(f, self.num_vertexes * 2)

        # Inner Edges on the opposite side of the road
        self.l_boundaries = Vector3.readn(f, self.num_vertexes)
        self.stop_light_pos = Vector3.readn(f, 2)
        self.lane_widths = read_unpack(f, '<5f')
        self.lane_lengths = read_unpack(f, '<10f')

    def read(f: BinaryIO) -> 'aiStreet':
        result = aiStreet()
        result.load(f)
        return result