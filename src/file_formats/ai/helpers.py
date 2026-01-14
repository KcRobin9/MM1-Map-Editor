from typing import List

from src.io.binary import read_unpack
from src.core.vector.vector_3 import Vector3


def read_array_list(f) -> List[int]:
    num_items, = read_unpack(f, '<I')
    return read_unpack(f, f'<{num_items}I')


class MiniParser:
    def __init__(self, file):
        self.file = file
        self.indent = 0
        self.newline = False

    def print(self, data):
        if self.newline:
            self.file.write(' ' * (self.indent * 4))
            self.newline = False

        self.file.write(data)
        if data.endswith('\n'):
            self.newline = True

    def begin_class(self, name):
        self.print(f'{name} :0 {{\n')
        self.indent += 1

    def value(self, value):
        if isinstance(value, list):
            self.print('[\n')
            self.indent += 1
            for val in value:
                self.value(val)
                self.print('\n')
            self.indent -= 1
            self.print(']')
            
        elif isinstance(value, str):            
            escaped_value = value.replace('\\', '\\\\').replace('"', '\\"')
            self.print(f'"{escaped_value}"')
            
        elif isinstance(value, int):
            self.print(str(value))
            
        elif isinstance(value, float):
            self.print(f"{value:.2f}")
                    
        elif isinstance(value, tuple):
            formatted_values = ', '.join(f"{v:.2f}" if isinstance(v, float) else str(v) for v in value)
            self.print(f'({formatted_values})')
                                
        elif isinstance(value, Vector3):
            self.print(f'{value.x:.2f} {value.y:.2f} {value.z:.2f}')
            
        else:
            raise Exception(f'Invalid Value Type {type(value)}')

    def field(self, name, value):
        self.print(f'{name} ')
        self.value(value)
        self.print('\n')

    def end_class(self):
        self.indent -= 1
        self.print('}\n')