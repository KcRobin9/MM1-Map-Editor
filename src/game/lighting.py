import csv
from pathlib import Path
from typing import List, Tuple, Union


LIGHTING_HEADER = [
    "TimeOfDay", "Weather", "Sun Heading", "Sun Pitch", "Sun Red", "Sun Green", "Sun Blue",
    "Fill-1 Heading", "Fill-1 Pitch", "Fill-1 Red", "Fill-1 Green", "Fill-1 Blue",
    "Fill-2 Heading", "Fill-2 Pitch", "Fill-2 Red", "Fill-2 Green", "Fill-2 Blue",
    "Ambient Red", "Ambient Green", "Ambient Blue", 
    "Fog End", "Fog Red", "Fog Green", "Fog Blue", 
    "Shadow Alpha", "Shadow Red", "Shadow Green", "Shadow Blue"
]


class Lighting:
    def __init__(self, time_of_day: int, weather: int, 
                 sun_heading: float, sun_pitch: float, sun_color: Tuple[float, float, float], 
                 fill_1_heading: float, fill_1_pitch: float, fill_1_color: Tuple[float, float, float], 
                 fill_2_heading: float, fill_2_pitch: float, fill_2_color: Tuple[float, float, float], 
                 ambient_color: Tuple[float, float, float],  
                 fog_end: float, fog_color: Tuple[float, float, float], 
                 shadow_alpha: float, shadow_color: Tuple[float, float, float]) -> None:
        
        self.time_of_day = time_of_day
        self.weather = weather
        self.sun_heading = sun_heading
        self.sun_pitch = sun_pitch
        self.sun_color = sun_color
        self.fill_1_heading = fill_1_heading
        self.fill_1_pitch = fill_1_pitch
        self.fill_1_color = fill_1_color
        self.fill_2_heading = fill_2_heading
        self.fill_2_pitch = fill_2_pitch
        self.fill_2_color = fill_2_color
        self.ambient_color = ambient_color
        self.fog_end = fog_end
        self.fog_color = fog_color
        self.shadow_alpha = shadow_alpha
        self.shadow_color = shadow_color

    @classmethod
    def read_rows(cls, row: list[Union[int, float, str]]) -> 'Lighting':
        return cls(
            time_of_day = int(row[0]),
            weather = int(row[1]),
            sun_heading = float(row[2]),
            sun_pitch = float(row[3]),
            sun_color = (float(row[4]), float(row[5]), float(row[6])),
            fill_1_heading = float(row[7]),
            fill_1_pitch = float(row[8]),
            fill_1_color = (float(row[9]), float(row[10]), float(row[11])),
            fill_2_heading = float(row[12]),
            fill_2_pitch = float(row[13]),
            fill_2_color = (float(row[14]), float(row[15]), float(row[16])),
            ambient_color = (float(row[17]), float(row[18]), float(row[19])),
            fog_end = float(row[20]),
            fog_color = (float(row[21]), float(row[22]), float(row[23])),
            shadow_alpha = float(row[24]),
            shadow_color = (float(row[25]), float(row[26]), float(row[27]))
        )

    @classmethod
    def read_all(cls, filename: Path) -> List['Lighting']:
        with open(filename, newline = "") as f:
            reader = csv.reader(f)
            next(reader)
            return [cls.read_rows(row) for row in reader]

    def apply_changes(self, changes: dict) -> None:
        for attribute, new_value in changes.items():
            if hasattr(self, attribute):
                current_value = getattr(self, attribute)
                if isinstance(current_value, tuple) and isinstance(new_value, tuple):
                    updated_value = tuple(
                        new_value[i] if i < len(new_value) else current_value[i]
                        for i in range(len(current_value))
                    )
                    setattr(self, attribute, updated_value)
                else:
                    setattr(self, attribute, new_value)

    @staticmethod
    def process_changes(instances: List['Lighting'], config_list: list) -> List['Lighting']:
        for config in config_list:
            for instance in instances:
                if instance.time_of_day == config["time_of_day"] and instance.weather == config["weather"]:
                    instance.apply_changes(config)
        return instances

    def write_rows(self) -> list:
        def fmt(value):
            return int(value) if isinstance(value, float) and value.is_integer() else value

        return [
            fmt(self.time_of_day),
            fmt(self.weather),
            fmt(self.sun_heading),
            fmt(self.sun_pitch),
            *map(fmt, self.sun_color),
            fmt(self.fill_1_heading),
            fmt(self.fill_1_pitch),
            *map(fmt, self.fill_1_color),
            fmt(self.fill_2_heading),
            fmt(self.fill_2_pitch),
            *map(fmt, self.fill_2_color),
            *map(fmt, self.ambient_color),
            fmt(self.fog_end),
            *map(fmt, self.fog_color),
            fmt(self.shadow_alpha),
            *map(fmt, self.shadow_color)
        ]

    @classmethod
    def write_all(cls, instances: List['Lighting'], lighting_configs: list, filename: Path) -> None:
        cls.process_changes(instances, lighting_configs)

        with open(filename, mode = "w", newline = "") as f:
            writer = csv.writer(f)
            writer.writerow(LIGHTING_HEADER)
            for instance in instances:
                writer.writerow(instance.write_rows())

        # if lighting_configs:
        #     config_details = [f"Time {c['time_of_day']}/Weather {c['weather']}" for c in lighting_configs]
        #     print(f"Successfully created lighting file with {len(lighting_configs)} modified config(s) ({', '.join(config_details)})")
        # else:
        #     print("Successfully created lighting file (no modifications)")

    @staticmethod
    def debug(instances: List['Lighting'], output_file: Path, debug_lighting: bool) -> None:
        if not debug_lighting:
            return

        if not output_file.parent.exists():
            print(f"The output folder {output_file.parent} does not exist. Creating it.")
            output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, "w") as f:
            for instance in instances:
                f.write(repr(instance))

    @classmethod
    def debug_file(cls, input_file: Path, output_file: Path, debug_lighting_file: bool) -> None:
        if not debug_lighting_file:
            return
        
        if not input_file.exists():
            print(f"The file {input_file} does not exist.")
            return
        
        if not output_file.parent.exists():
            print(f"The output folder {output_file.parent} does not exist. Creating it.")
            output_file.parent.mkdir(parents=True, exist_ok=True)
        instances = cls.read_all(input_file)

        with open(output_file, "w") as f:
            for instance in instances:
                f.write(repr(instance))

        print(f"Processed {input_file.name} to {output_file.name}")

    def __repr__(self) -> str:
        return f"""
LIGHTING
    Time of Day: {self.time_of_day}
    Weather: {self.weather}
    Sun Heading: {self.sun_heading:.2f}
    Sun Pitch: {self.sun_pitch:.2f}
    Sun Color: {self.sun_color}
    Fill 1 Heading: {self.fill_1_heading:.2f}
    Fill 1 Pitch: {self.fill_1_pitch:.2f}
    Fill 1 Color: {self.fill_1_color}
    Fill 2 Heading: {self.fill_2_heading:.2f}
    Fill 2 Pitch: {self.fill_2_pitch:.2f}
    Fill 2 Color: {self.fill_2_color}
    Ambient Color: {self.ambient_color}
    Fog End: {self.fog_end:.2f}
    Fog Color: {self.fog_color}
    Shadow Alpha: {self.shadow_alpha:.2f}
    Shadow Color: {self.shadow_color}
    """