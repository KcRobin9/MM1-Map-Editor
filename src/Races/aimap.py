from pathlib import Path
from typing import Dict, List, Tuple, Any

from src.races.formatters import write_section, format_exceptions, format_police_data, format_opponent_data


def prepare_aimap_data(config: Dict[str, Any], race_type: str, race_index: int, opponents: Dict[str, List[List[float]]]) -> Tuple[float, int, str, str, str]:
    traffic_density = config.get("traffic_density", 0.0)
    speed_limit = config.get("speed_limit", 45)
    
    exceptions = config.get("exceptions", [])
    exception_count = config.get("num_of_exceptions", len(exceptions))
        
    police_data = config["police"]
    num_of_police = config["num_of_police"]

    exceptions_data_formatted = format_exceptions(exceptions, exception_count)
    police_data_formatted = format_police_data(police_data, num_of_police)
    opponent_data_formatted = format_opponent_data(opponents, race_type, race_index)
    
    return (traffic_density, speed_limit, exceptions_data_formatted, police_data_formatted, opponent_data_formatted)


def write_aimap(output_file: Path, traffic_density: float, speed_limit: int, exceptions_data_formatted: str, police_data_formatted: str, opponent_data_formatted: str, num_of_opponents: int) -> None:
    with open(output_file, "w") as f:
        
        template = f"""
# Ambient Traffic Density 
[Density] 
{traffic_density}

# Default Road Speed Limit 
[Speed Limit] 
{speed_limit} 

# Ambient Traffic Exceptions
# Rd Id, Density, Speed Limit 
"""
        f.write(template)
            
        write_section(f, "[Exceptions]", exceptions_data_formatted)
        write_section(f, "[Police]", police_data_formatted)
        write_section(f, "[Opponent]", f"{num_of_opponents}\n{opponent_data_formatted}")