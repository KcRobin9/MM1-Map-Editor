from typing import Dict, Any

from src.constants.modes import RaceMode
from src.constants.misc import Folder
from src.constants.file_formats import FileType

from src.game.races.checks import check_race_count, check_waypoint_count
from src.game.races.aimap import prepare_aimap_data, write_aimap
from src.game.races.mm_data import write_mm_data_header, write_mm_data
from src.game.races.constants import RACE_TYPE_TO_EXTENSION, RACE_TYPE_TO_PREFIX, CHECKPOINT_PREFIXES
from src.game.races.constants_2 import MM_DATA_FILES
from src.game.waypoints.waypoints import write_waypoints


def create_races(race_data: Dict[str, Dict[str, Any]]) -> None:
    mm_data_written = {
        RaceMode.CHECKPOINT: False,
        RaceMode.CIRCUIT: False,
        RaceMode.BLITZ: False
    }
    
    race_counts = {
        RaceMode.CHECKPOINT: 0,
        RaceMode.CIRCUIT: 0,
        RaceMode.BLITZ: 0
    }
    
    for race_key, config in race_data.items():
        race_type, race_index = race_key.split("_", 1)
        race_index = int(race_index)
        
        # Count this race
        race_counts[race_type] += 1

        player_waypoints = config["player_waypoints"]
                
        ai_map = config["aimap"]
        opponents = ai_map["opponents"]
        
        # Handle both dict and list formats for opponents
        if isinstance(opponents, dict):
            opponent_list = [(car_name, waypoints) for car_name, waypoints in opponents.items()]
        else:
            opponent_list = [(list(opp.keys())[0], list(opp.values())[0]) for opp in opponents]
        
        num_of_opponents = ai_map.get("num_of_opponents", len(opponent_list))

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
        
        # Opponent Waypoints - iterate through all opponents
        for opp_index, (opp_car_name, opp_waypoints) in enumerate(opponent_list):
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

    # Build the race breakdown
    total_races = sum(race_counts.values())
    breakdown_parts = []
    if race_counts[RaceMode.CHECKPOINT] > 0:
        breakdown_parts.append(f"checkpoint: {race_counts[RaceMode.CHECKPOINT]}")
    if race_counts[RaceMode.BLITZ] > 0:
        breakdown_parts.append(f"blitz: {race_counts[RaceMode.BLITZ]}")
    if race_counts[RaceMode.CIRCUIT] > 0:
        breakdown_parts.append(f"circuit: {race_counts[RaceMode.CIRCUIT]}")
    
    if breakdown_parts:
        breakdown = ", ".join(breakdown_parts)
        print(f"Successfully created {total_races} race file(s) ({breakdown})")
    else:
        print(f"Successfully created 0 race file(s)")