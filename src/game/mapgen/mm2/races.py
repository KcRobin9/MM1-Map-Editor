"""
MM2 race files -> MM1 race files. Converts a city's blitz / checkpoint / circuit races so they are
selectable in MM1 with the SAME spawn and checkpoints as MM2 (for side-by-side screenshots).

MM2 and MM1 share the format almost exactly:
- waypoints: MM2 `x,y,z,a,radius,framerate,statechanges,texchanges,msg` -> MM1 `x,y,z,a,radius,0,0,`
  (MM1 drops the framerate column). Coords are the same world frame as the pass-through geometry, so
  no transform is needed.
- naming: MM2 blitzN / raceN / circuitN -> MM1 BLITZN / RACEN (checkpoint) / CIRCUITN.
- aimap: same INI, so the MM2 file copies across with cops and opponents zeroed (see _aimap_to_mm1).
"""
import re
from pathlib import Path
from typing import List, Optional

from src.constants.mm2 import Mm2RaceType
from src.constants.misc import Threshold
from src.constants.file_formats import FileType
from src.game.races.aimap import write_aimap
from src.game.races.checks import RACE_TYPE_LIMIT
from src.game.races.constants import MM_DATA_HEADER
from src.game.races.constants_2 import MM_DATA_FILES
from src.game.races.formatters import format_exceptions, format_police_data
from src.game.waypoints.waypoints import write_waypoints

DEFAULT_SPEED_LIMIT = 30    # only used for the fallback aimap; a real MM2 aimap brings its own

# Roster column indices, amateur block then pro block (both blocks share the same layout).
OPPONENTS_COLUMNS = (4, 14)
COPS_COLUMNS = (5, 15)
AMBIENT_COLUMN = 6
NUM_LAPS_COLUMNS = (8, 18)
ROSTER_COLUMNS = 16         # a row shorter than this is malformed and left alone

DEFAULT_AMBIENT_DENSITY = 0.3
MIN_WAYPOINT_FIELDS = 5     # x, y, z, angle, radius


def _read_rows(path: Path) -> List[str]:
    """Non-empty lines of a MM2 CSV. MM2 ships these latin-1, not utf-8."""
    return [line for line in path.read_text(encoding = "latin-1").splitlines() if line.strip()]


def _read_waypoints(path: Path) -> List[List[float]]:
    """MM2 waypoint CSV -> [[x, y, z, angle, radius]], dropping the header and any short row."""
    waypoints = []

    for line in _read_rows(path)[1:]:               # row 0 is MM2's own header
        columns = line.split(",")
        if len(columns) < MIN_WAYPOINT_FIELDS:
            continue
        waypoints.append([float(value) for value in columns[:MIN_WAYPOINT_FIELDS]])

    return waypoints


def parse_mm2_cinfo(cinfo_path: str) -> dict:
    """Read the MM2 city .cinfo for the real race names -> {blitz/circuit/checkpoint: [names]}.

    The cinfo is authoritative on COUNT: a city can ship leftover waypoint files beyond the races it
    actually offers, and those must not become playable entries.
    """
    names = {"blitz": [], "circuit": [], "checkpoint": []}
    keys = {"BlitzNames": "blitz", "CircuitNames": "circuit", "CheckpointNames": "checkpoint"}

    for line in Path(cinfo_path).read_text(encoding = "latin-1").splitlines():
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        if key.strip() in keys:
            names[keys[key.strip()]] = [name.strip() for name in value.split("|") if name.strip()]

    return names


def _aimap_to_mm1(mm2_aimap_path: Path, ambient_density: float) -> str:
    """MM2 <type><index>.aimap -> MM1 aimap text.

    MM1 and MM2 are the same engine, so [Speed Limit] / [Exceptions] copy verbatim. Two changes:
    a [Density] section is prepended (MM2 aimaps omit it, the MM1 loader expects it), and [Police]
    and [Opponent] are zeroed. Cops still hit the aiVehiclePolice::Reset crash, and raw MM2 opponent
    lines snap to non-adjacent intersections in OUR BAI network, crashing aiVehicleOpponent::Init.
    Both need work of their own; ambient traffic already works and stays.
    """
    lines = mm2_aimap_path.read_text(encoding = "latin-1").splitlines()
    out = ["[Density]", "%.2f" % ambient_density, ""]
    index = 0

    while index < len(lines):
        if lines[index].strip() not in ("[Police]", "[Opponent]"):
            out.append(lines[index])
            index += 1
            continue

        out.append(lines[index])
        index += 1

        # The section header is followed by a count, then that many entry lines. Emit a count of
        # zero and skip the entries.
        count_line = lines[index].strip() if index < len(lines) else ""
        entry_count = int(count_line) if count_line.lstrip("-").isdigit() else 0
        out.append("0")
        index += 1 + entry_count

    return "\n".join(out) + "\n"


def _convert_roster(source_csv: Path, destination_csv: Path, selected: List[int],
                    num_laps_overrides: Optional[List] = None) -> List[float]:
    """Copy MM2's mm<type>data.csv roster to MM1, keeping the real opponent/ambient/peds/lap values.

    `selected` is the MM2 race indices being imported, in output order, so a dropped race takes its
    roster row with it and row N still describes race N. Opponents and cops are forced to 0 for the
    reasons in _aimap_to_mm1. Returns the per-race ambient density for the matching aimap.
    """
    rows = _read_rows(source_csv)
    # MM2's own header matches MM1's column-for-column, but emit the canonical one so a city that
    # ships a different header cannot silently produce a roster MM1 misreads.
    out = [",".join(["Description"] + MM_DATA_HEADER * 2)]
    ambient_densities = []

    data_rows = rows[1:]
    for race_index, mm2_index in enumerate(selected):
        if mm2_index >= len(data_rows):
            continue

        columns = [value.strip() for value in data_rows[mm2_index].split(",")]

        if len(columns) >= ROSTER_COLUMNS:
            for column in OPPONENTS_COLUMNS + COPS_COLUMNS:
                columns[column] = "0"

        # MM1 blitz requires hitting ALL gates in order, while MM2's NumLaps is a "hit N of M"
        # count. A mismatch overflows the heap in mmWaypoints::LoadCSV, so it is overridden with
        # the real waypoint-row count.
        if num_laps_overrides and race_index < len(num_laps_overrides):
            override = num_laps_overrides[race_index]
            if override is not None:
                for column in NUM_LAPS_COLUMNS:
                    if len(columns) > column:
                        columns[column] = str(override)

        has_ambient = len(columns) > AMBIENT_COLUMN and columns[AMBIENT_COLUMN]
        ambient_densities.append(float(columns[AMBIENT_COLUMN]) if has_ambient
                                 else DEFAULT_AMBIENT_DENSITY)
        out.append(",".join(columns))

    destination_csv.write_text("\n".join(out) + "\n")

    return ambient_densities


def _find_waypoint_files(mm2_dir: Path, race_type: str) -> dict:
    """{race index: waypoint csv} for one race type, read from the MM2 file names."""
    found = {}
    pattern = re.compile(rf"{race_type}(\d+)waypoints\.csv$", re.I)

    for path in mm2_dir.glob(f"{race_type}*waypoints.csv"):
        match = pattern.match(path.name)
        if match:
            found[int(match.group(1))] = path

    return found


def _race_limit(race_type: str):
    """The editor's own RaceInfo for this type: its display name and how many MM1 can hold."""
    return RACE_TYPE_LIMIT.get(Mm2RaceType.TO_RACE_MODE[race_type])


def _write_fallback_aimap(output_file: Path) -> None:
    """A race with no MM2 aimap to copy gets a bare one: no traffic, cops or opponents.

    Written through the editor's own write_aimap so it carries the same section comments the game's
    files do, and so the layout only has to be right in one place.
    """
    write_aimap(output_file, traffic_density = 0, speed_limit = DEFAULT_SPEED_LIMIT,
                exceptions_data_formatted = format_exceptions(),
                police_data_formatted = format_police_data([], 0),
                opponent_data_formatted = "", num_of_opponents = 0)


def _selected_races(race_type: str, waypoints_by_index: dict, race_count: int, log) -> List[int]:
    """MM2 race indices to import, in order, after applying MM1's limits.

    MM2 ships races MM1 cannot hold: SF blitz 4 has 14 gates and London blitz 9 has 23, against a
    ceiling of Threshold.BLITZ_WAYPOINT_COUNT. Those are dropped with a warning rather than raised
    on, so one oversized MM2 race cannot cost you the city's whole race set.
    """
    selected = []

    for index in range(race_count):
        if index not in waypoints_by_index:
            continue

        gate_count = len(waypoints_by_index[index])
        if race_type == "blitz" and gate_count > Threshold.BLITZ_WAYPOINT_COUNT:
            if log:
                log(f"mm2 races: skipped blitz {index} --- {gate_count} gates exceeds the "
                    f"{Threshold.BLITZ_WAYPOINT_COUNT}-gate MM1 limit")
            continue

        selected.append(index)

    limit = _race_limit(race_type)
    if limit and len(selected) > limit.threshold:
        if log:
            log(f"mm2 races: {len(selected)} {limit.name} races exceed MM1's {limit.threshold} "
                f"slots --- importing the first {limit.threshold}")
        selected = selected[:limit.threshold]

    return selected


def convert_mm2_races(mm2_dir: str, out_dir: str, cinfo_path: str = "", log = None) -> tuple:
    """Convert the blitz/checkpoint/circuit races in `mm2_dir` into MM1 race files under `out_dir`.

    Writes the player waypoints, the real MM2 aimaps (ambient kept, cops and opponents stripped) and
    the real rosters. Returns (blitz_names, checkpoint_names, circuit_names, waypoint_counts) for the
    CINFO the build registers.

    Surviving races are RENUMBERED consecutively from 0. A race MM1 cannot hold is dropped, and
    leaving a hole would desync the CINFO's Nth name from the on-disk file <TYPE>N.
    """
    mm2_dir, out_dir = Path(mm2_dir), Path(out_dir)
    out_dir.mkdir(parents = True, exist_ok = True)

    mm2_names = parse_mm2_cinfo(cinfo_path) if cinfo_path else {}
    names = {race_type: [] for race_type in Mm2RaceType.ALL}
    waypoint_counts = {}

    for race_type in Mm2RaceType.ALL:
        waypoint_files = _find_waypoint_files(mm2_dir, race_type)
        real_names = mm2_names.get(Mm2RaceType.TO_CINFO_KEY[race_type], [])
        race_count = len(real_names) if real_names else len(waypoint_files)

        waypoints_by_index = {index: _read_waypoints(path)
                              for index, path in waypoint_files.items()}
        selected = _selected_races(race_type, waypoints_by_index, race_count, log)

        # The roster must line up row-for-row with the races actually written, so it is filtered to
        # the same selection. Blitz NumLaps must equal the gate count --- see _convert_roster.
        num_laps_overrides = ([len(waypoints_by_index[index]) for index in selected]
                              if race_type == "blitz" else None)

        source_roster = mm2_dir / f"mm{race_type}data{FileType.CSV.lower()}"
        if source_roster.exists():
            roster_name = MM_DATA_FILES[Mm2RaceType.TO_RACE_MODE[race_type]].name
            ambient_densities = _convert_roster(source_roster, out_dir / roster_name,
                                                selected, num_laps_overrides)
        else:
            ambient_densities = [DEFAULT_AMBIENT_DENSITY] * len(selected)

        race_mode = Mm2RaceType.TO_RACE_MODE[race_type]
        for out_index, mm2_index in enumerate(selected):
            prefix = f"{race_mode}{out_index}"
            waypoints = waypoints_by_index[mm2_index]
            write_waypoints(out_dir / f"{prefix}WAYPOINTS{FileType.CSV}", waypoints,
                            race_mode, out_index)

            ambient = (ambient_densities[out_index] if out_index < len(ambient_densities)
                       else DEFAULT_AMBIENT_DENSITY)
            # The engine reads the base .AIMAP on default difficulty and _P on the harder ones.
            source_aimap = mm2_dir / f"{race_type}{mm2_index}.aimap"
            for extension in (".AIMAP", ".AIMAP_P"):
                output_file = out_dir / (prefix + extension)
                if source_aimap.exists():
                    output_file.write_text(_aimap_to_mm1(source_aimap, ambient))
                else:
                    _write_fallback_aimap(output_file)

            fallback_name = f"{_race_limit(race_type).name} {out_index}"
            names[race_type].append(real_names[mm2_index] if mm2_index < len(real_names)
                                    else fallback_name)
            waypoint_counts[(race_type, out_index)] = len(waypoints)

    return names["blitz"], names["race"], names["circuit"], waypoint_counts
