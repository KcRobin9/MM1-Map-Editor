import csv
from pathlib import Path
from typing import Tuple, Union


LIGHTING_HEADER = [
    "TimeOfDay", "Weather", "Sun Heading", "Sun Pitch", "Sun Red", "Sun Green", "Sun Blue",
    "Fill-1 Heading", "Fill-1 Pitch", "Fill-1 Red", "Fill-1 Green", "Fill-1 Blue",
    "Fill-2 Heading", "Fill-2 Pitch", "Fill-2 Red", "Fill-2 Green", "Fill-2 Blue",
    "Ambient Red", "Ambient Green", "Ambient Blue", 
    "Fog End", "Fog Red", "Fog Green", "Fog Blue", 
    "Shadow Alpha", "Shadow Red", "Shadow Green", "Shadow Blue"
]


class LightingEditor:
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
    def read_rows(cls, row: list[Union[int, float, str]]) -> 'LightingEditor':
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
    def read_file(cls, filename: Path):
        instances = []
        
        with open(filename, newline = "") as f:
            reader = csv.reader(f)
            next(reader)  
            
            for data in reader:
                instance = cls.read_rows(data)
                instances.append(instance)
                
        return instances
        
    def apply_changes(self, changes):
        for attribute, new_value in changes.items():
            if hasattr(self, attribute):
                current_value = getattr(self, attribute)
                
                if isinstance(current_value, tuple) and isinstance(new_value, tuple):
                    # Update only the specified components for tuple attributes
                    updated_value = tuple(new_value[i] if i < len(new_value) else current_value[i] for i in range(len(current_value)))
                    setattr(self, attribute, updated_value)
                else:
                    setattr(self, attribute, new_value)
            
    @staticmethod
    def process_changes(instances, config_list):
        for config in config_list:
            for instance in instances:
                if instance.time_of_day == config["time_of_day"] and instance.weather == config["weather"]:
                    instance.apply_changes(config)
        return instances
                
    def write_rows(self):
        def format_value(value):
            return int(value) if isinstance(value, float) and value.is_integer() else value

        return [
            format_value(self.time_of_day),
            format_value(self.weather),
            format_value(self.sun_heading),
            format_value(self.sun_pitch),
            *map(format_value, self.sun_color),
            format_value(self.fill_1_heading),
            format_value(self.fill_1_pitch),
            *map(format_value, self.fill_1_color),
            format_value(self.fill_2_heading),
            format_value(self.fill_2_pitch),
            *map(format_value, self.fill_2_color),
            *map(format_value, self.ambient_color),
            format_value(self.fog_end),
            *map(format_value, self.fog_color),
            format_value(self.shadow_alpha),
            *map(format_value, self.shadow_color)
        ]
        
    @classmethod
    def write_file(cls, instances, lighting_configs, filename: Path):
        cls.process_changes(instances, lighting_configs)
        
        with open(filename, mode = "w", newline = "") as f:
            writer = csv.writer(f)        
            writer.writerow(LIGHTING_HEADER)
            
            for instance in instances:
                writer.writerow(instance.write_rows())
                
    @classmethod
    def debug(cls, instances, debug_file: str, debug_lighting: bool) -> None:
        if not debug_lighting:
            return

        with open(debug_file, "w") as debug_f:
            for instance in instances:
                debug_f.write(instance.__repr__())
                debug_f.write("\n")
                
    def __repr__(self):
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
    def read_rows(cls, row: list[Union[int, float, str]]) -> 'LightingEditor':
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
    def read_file(cls, filename: Path):
        instances = []
        
        with open(filename, newline = "") as f:
            reader = csv.reader(f)
            next(reader)  
            
            for data in reader:
                instance = cls.read_rows(data)
                instances.append(instance)
                
        return instances
        
    def apply_changes(self, changes):
        for attribute, new_value in changes.items():
            if hasattr(self, attribute):
                current_value = getattr(self, attribute)
                
                if isinstance(current_value, tuple) and isinstance(new_value, tuple):
                    # Update only the specified components for tuple attributes
                    updated_value = tuple(new_value[i] if i < len(new_value) else current_value[i] for i in range(len(current_value)))
                    setattr(self, attribute, updated_value)
                else:
                    setattr(self, attribute, new_value)
            
    @staticmethod
    def process_changes(instances, config_list):
        for config in config_list:
            for instance in instances:
                if instance.time_of_day == config["time_of_day"] and instance.weather == config["weather"]:
                    instance.apply_changes(config)
        return instances
                
    def write_rows(self):
        def format_value(value):
            return int(value) if isinstance(value, float) and value.is_integer() else value

        return [
            format_value(self.time_of_day),
            format_value(self.weather),
            format_value(self.sun_heading),
            format_value(self.sun_pitch),
            *map(format_value, self.sun_color),
            format_value(self.fill_1_heading),
            format_value(self.fill_1_pitch),
            *map(format_value, self.fill_1_color),
            format_value(self.fill_2_heading),
            format_value(self.fill_2_pitch),
            *map(format_value, self.fill_2_color),
            *map(format_value, self.ambient_color),
            format_value(self.fog_end),
            *map(format_value, self.fog_color),
            format_value(self.shadow_alpha),
            *map(format_value, self.shadow_color)
        ]
        
    @classmethod
    def write_file(cls, instances, lighting_configs, filename: Path):
        cls.process_changes(instances, lighting_configs)
        
        with open(filename, mode = "w", newline = "") as f:
            writer = csv.writer(f)        
            writer.writerow(LIGHTING_HEADER)
            
            for instance in instances:
                writer.writerow(instance.write_rows())
                
    @classmethod
    def debug(cls, instances, debug_file: str, debug_lighting: bool) -> None:
        if not debug_lighting:
            return

        with open(debug_file, "w") as debug_f:
            for instance in instances:
                debug_f.write(instance.__repr__())
                debug_f.write("\n")
                
    def __repr__(self):
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