from typing import Dict, Any

from src.Constants.races import RaceMode, MM_DATA_FILES
from src.Constants.misc import Folder
from src.Constants.constants import RACE_TYPE_TO_EXTENSION, RACE_TYPE_TO_PREFIX, CHECKPOINT_PREFIXES
from src.Constants.file_types import FileType

from src.races.checks import check_race_count, check_waypoint_count
from src.races.aimap import prepare_aimap_data, write_aimap
from src.races.mm_data import write_mm_data_header, write_mm_data
from src.races.waypoints import write_waypoints


def create_races(race_data: Dict[str, Dict[str, Any]]) -> None:
    mm_data_written = {
        RaceMode.CHECKPOINT: False,
        RaceMode.CIRCUIT: False,
        RaceMode.BLITZ: False
    }
    
    for race_key, config in race_data.items():
        race_type, race_index = race_key.split("_", 1)
        race_index = int(race_index)

        player_waypoints = config["player_waypoints"]
                
        ai_map = config["aimap"]
        opponents = ai_map["opponents"]
        num_of_opponents = ai_map.get("num_of_opponents", len(opponents))

        prepared_aimap_data = prepare_aimap_data(ai_map, race_type, race_index, opponents)
                                    
        file_prefix = f"{race_type}{race_index}"

        ai_map_file = Folder.SHOP_RACE_MAP / f"{file_prefix}.AIMAP_P"
        player_waypoint_file = Folder.SHOP_RACE_MAP / f"{file_prefix}WAYPOINTS{FileType.CSV}"
        mm_data_file = MM_DATA_FILES[race_type]
        
        # Safety Checks
        check_race_count(race_type, config)
        check_waypoint_count(race_type, player_waypoints)
        
        # Player Waypoints
        write_waypoints(player_waypoint_file, player_waypoints, race_type, race_index)
        
        # Opponent Waypoints
        for opp_index, opp_waypoints in enumerate(opponents.values()):
            opp_file_name = f"OPP{opp_index}{file_prefix}{RACE_TYPE_TO_EXTENSION[race_type]}{race_index}"
            opp_waypoint_file = Folder.SHOP_RACE_MAP / opp_file_name
            write_waypoints(opp_waypoint_file, opp_waypoints, race_type, race_index, opp_index)
        
        # Write Header Only Once for Each File
        if not mm_data_written[race_type]:
            write_mm_data_header(mm_data_file)
            mm_data_written[race_type] = True
        
        # MM DATA
        if race_type == RaceMode.CHECKPOINT:
            write_mm_data(mm_data_file, {race_index: config}, race_type, CHECKPOINT_PREFIXES[race_index])
        else:
            write_mm_data(mm_data_file, {race_index: config}, race_type, RACE_TYPE_TO_PREFIX[race_type])
            
        # AI MAP                
        write_aimap(ai_map_file, *prepared_aimap_data, num_of_opponents)