"""
MM2 race files -> MM1 race files. Converts a city's blitz / checkpoint / circuit races so they are
selectable in MM1 with the SAME spawn and checkpoints as MM2 (for side-by-side screenshots).

MM2 and MM1 share the format almost exactly:
- waypoints: MM2 `x,y,z,a,radius,framerate,statechanges,texchanges,msg` -> MM1 `x,y,z,a,radius,0,0,`
  (MM1 drops the framerate column). Coords are the same world frame as the pass-through geometry, so
  no transform is needed.
- naming: MM2 blitzN / raceN / circuitN -> MM1 BLITZN / RACEN (checkpoint) / CIRCUITN.
- aimap: same INI, so the MM2 file copies across with cops zeroed (see _aimap_to_mm1).
- opponents: each MM2 <race>-<a|p>-<n>.opp route is snapped to OUR converted BAI
  junctions, validated hop-by-hop against the road graph bai_direct writes and repaired with the
  shortest road path where a hop has no single road (src/game/mapgen/mm2/opp_routes.py). Emitted in
  the editor's own OPP file format; [Opponent] + the roster's Opponents columns are re-enabled. Needs
  `bai_path` (the same .bai bai_direct converts); without it opponents stay off as before.
"""
import re
from pathlib import Path
from typing import List, Optional

from src.constants.mm2 import Mm2RaceType
from src.constants.misc import Threshold
from src.constants.file_formats import FileType
from src.game.races.aimap import write_aimap
from src.game.races.checks import RACE_TYPE_LIMIT
from src.game.races.constants import MM_DATA_HEADER, RACE_TYPE_TO_EXTENSION
from src.game.races.constants_2 import MM_DATA_FILES
from src.game.races.formatters import format_exceptions, format_police_data
from src.game.waypoints.waypoints import write_waypoints
from src.game.mapgen.mm2.opp_routes import (load_graph, read_opp_rows, convert_route, verify_route,
                                            parse_aimap_opponents, mm1_model)

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
        try:
            waypoints.append([float(value) for value in columns[:MIN_WAYPOINT_FIELDS]])
        except ValueError:        # e.g. Buenos Aires ships a "6.8.0" typo row; one bad gate != no races
            continue

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


def _aimap_to_mm1(mm2_aimap_path: Path, ambient_density: float,
                  opponent_lines: Optional[List[str]] = None) -> str:
    """MM2 <type><index>.aimap -> MM1 aimap text."""
    # Same engine, so [Speed Limit] and [Exceptions] copy verbatim. Three sections change:
    #   [Density]  prepended --- MM2 omits it, the MM1 loader expects it
    #   [Police]   zeroed    --- cops still hit the aiVehiclePolice::Reset crash
    #   [Opponent] replaced by opponent_lines, or zeroed when None. MM1's parser reads 3 fields and
    #              would mis-read MM2's 12-field lines as its optional Color/Avoid/Brake extensions.
    lines = mm2_aimap_path.read_text(encoding = "latin-1").splitlines()
    out = ["[Density]", "%.2f" % ambient_density, ""]
    index = 0

    while index < len(lines):
        if lines[index].strip() not in ("[Police]", "[Opponent]"):
            out.append(lines[index])
            index += 1
            continue

        section = lines[index].strip()
        out.append(lines[index])
        index += 1

        # The section header is followed by a count, then that many entry lines (comments and
        # blanks in between are skipped by the loader but still need skipping here).
        count_line = lines[index].strip() if index < len(lines) else ""
        entry_count = int(count_line) if count_line.lstrip("-").isdigit() else 0
        index += 1
        skipped = 0
        while skipped < entry_count and index < len(lines):
            if lines[index].strip() and not lines[index].lstrip().startswith("#"):
                skipped += 1
            index += 1

        if section == "[Opponent]" and opponent_lines:
            out.append(str(len(opponent_lines)))
            out.extend(opponent_lines)
        else:
            out.append("0")

    return "\n".join(out) + "\n"


def _opponent_file_name(race_mode: str, out_index: int, opp_index: int, pro: bool) -> str:
    """OPP<k><MODE><n>[P].<X>_<n>, e.g. OPP0RACE3.R_3 / OPP0RACE3P.R_3 (the editor's own convention
    plus a P marker for the pro roster, whose MM2 routes differ from the amateur ones)."""
    suffix = "P" if pro else ""
    return f"OPP{opp_index}{race_mode}{out_index}{suffix}{RACE_TYPE_TO_EXTENSION[race_mode]}{out_index}"


def _convert_opponents(mm2_dir: Path, out_dir: Path, source_aimap: Path, graph, race_type: str,
                       race_mode: str, out_index: int, pro: bool, log, stats: dict) -> List[str]:
    """The [Opponent] lines for one race/difficulty, writing the OPP route files.

    Every MM2 .opp the aimap names is snapped + validated + repaired over `graph`; a route that
    cannot be made graph-valid is dropped (logged), so the count always matches the files written.
    """
    lines = []
    for opp_index, (mm2_model, opp_name, throttle) in enumerate(parse_aimap_opponents(source_aimap)):
        opp_path = mm2_dir / opp_name
        if not opp_path.exists():
            stats["missing"] += 1
            continue

        label = f"{race_type}{out_index}{'p' if pro else 'a'}:{opp_name}"
        route = convert_route(read_opp_rows(opp_path), graph, log, label)
        if route is None:
            stats["dropped"] += 1
            continue

        problems = verify_route(route["rows"], graph)
        if problems:                                   # the checker must never let a bad route ship
            stats["dropped"] += 1
            if log:
                log(f"opp {label}: verify failed: {problems[0]}")
            continue

        file_name = _opponent_file_name(race_mode, out_index, len(lines), pro)
        write_waypoints(out_dir / file_name, route["rows"], race_mode, out_index, len(lines))
        lines.append(f"{mm1_model(mm2_model)} {file_name} {throttle:.2f}")
        stats["written"] += 1
        stats["repaired_hops"] += route["repaired"]
        stats["inserted"] += route["inserted"]
        stats["far_snaps"] += route["far_snaps"]

    return lines


def _convert_roster(source_csv: Path, destination_csv: Path, selected: List[int],
                    num_laps_overrides: Optional[List] = None,
                    opponent_counts: Optional[List[tuple]] = None) -> List[float]:
    """Copy MM2's mm<type>data.csv roster to MM1, keeping the real opponent/ambient/peds/lap values.

    `selected` is the MM2 race indices being imported, in output order, so a dropped race takes its
    roster row with it and row N still describes race N. Cops are forced to 0 (see _aimap_to_mm1).
    Opponents: `opponent_counts[race] = (amateur, pro)` = the routes actually written;
    None or a missing entry forces 0 like before. Returns the per-race ambient density for the
    matching aimap.
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
            for column in COPS_COLUMNS:
                columns[column] = "0"
            counts = (opponent_counts[race_index] if opponent_counts and race_index < len(opponent_counts)
                      else (0, 0))
            for column, count in zip(OPPONENTS_COLUMNS, counts):
                columns[column] = str(count)

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


def convert_mm2_races(mm2_dir: str, out_dir: str, cinfo_path: str = "", log = None,
                      bai_path: str = None, one_way_mode: str = "blocked") -> tuple:
    """Convert the races in `mm2_dir` into MM1 race files under `out_dir`.

    Returns (blitz_names, checkpoint_names, circuit_names, waypoint_counts) for the CINFO.
    """
    # Writes the player waypoints, the MM2 aimaps (ambient kept, cops stripped) and the rosters.
    # `bai_path` additionally converts the MM2 opponent routes, graph-valid over the network
    # bai_direct writes from that .bai using the same `one_way_mode`.
    #
    # Surviving races are RENUMBERED consecutively from 0: a race MM1 cannot hold is dropped, and
    # leaving a hole would desync the CINFO's Nth name from the on-disk file <TYPE>N.
    mm2_dir, out_dir = Path(mm2_dir), Path(out_dir)
    out_dir.mkdir(parents = True, exist_ok = True)

    mm2_names = parse_mm2_cinfo(cinfo_path) if cinfo_path else {}
    names = {race_type: [] for race_type in Mm2RaceType.ALL}
    waypoint_counts = {}

    graph = None
    if bai_path and Path(bai_path).exists():
        graph = load_graph(bai_path, one_way_mode = one_way_mode)
    opp_stats = {"written": 0, "dropped": 0, "missing": 0, "repaired_hops": 0, "inserted": 0,
                 "far_snaps": 0}

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

        race_mode = Mm2RaceType.TO_RACE_MODE[race_type]

        # Ambient density comes from the roster, but the roster also needs the opponent counts, which
        # only exist once the routes are converted: read the densities first, write the roster last.
        source_roster = mm2_dir / f"mm{race_type}data{FileType.CSV.lower()}"
        roster_rows = _read_rows(source_roster)[1:] if source_roster.exists() else []
        ambient_densities = []
        for mm2_index in selected:
            columns = ([value.strip() for value in roster_rows[mm2_index].split(",")]
                       if mm2_index < len(roster_rows) else [])
            has_ambient = len(columns) > AMBIENT_COLUMN and columns[AMBIENT_COLUMN]
            ambient_densities.append(float(columns[AMBIENT_COLUMN]) if has_ambient
                                     else DEFAULT_AMBIENT_DENSITY)

        opponent_counts = []
        for out_index, mm2_index in enumerate(selected):
            prefix = f"{race_mode}{out_index}"
            waypoints = waypoints_by_index[mm2_index]
            write_waypoints(out_dir / f"{prefix}WAYPOINTS{FileType.CSV}", waypoints,
                            race_mode, out_index)

            ambient = (ambient_densities[out_index] if out_index < len(ambient_densities)
                       else DEFAULT_AMBIENT_DENSITY)
            # The engine reads the base .AIMAP on default difficulty and _P on the harder ones; MM2
            # ships a separate aimap_p (pro roster + its own -p- routes) where the race has one.
            counts = []
            for extension, pro in ((".AIMAP", False), (".AIMAP_P", True)):
                source_aimap = mm2_dir / f"{race_type}{mm2_index}.aimap{'_p' if pro else ''}"
                if not source_aimap.exists():
                    source_aimap = mm2_dir / f"{race_type}{mm2_index}.aimap"
                output_file = out_dir / (prefix + extension)
                if source_aimap.exists():
                    opponent_lines = (_convert_opponents(mm2_dir, out_dir, source_aimap, graph, race_type,
                                                         race_mode, out_index, pro, log, opp_stats)
                                      if graph else [])
                    output_file.write_text(_aimap_to_mm1(source_aimap, ambient, opponent_lines))
                    counts.append(len(opponent_lines))
                else:
                    _write_fallback_aimap(output_file)
                    counts.append(0)
            opponent_counts.append(tuple(counts))

            fallback_name = f"{_race_limit(race_type).name} {out_index}"
            names[race_type].append(real_names[mm2_index] if mm2_index < len(real_names)
                                    else fallback_name)
            waypoint_counts[(race_type, out_index)] = len(waypoints)

        if source_roster.exists():
            roster_name = MM_DATA_FILES[race_mode].name
            _convert_roster(source_roster, out_dir / roster_name, selected, num_laps_overrides,
                            opponent_counts)

    if log and graph:
        log(f"mm2 races: opponents {opp_stats['written']} routes written, {opp_stats['dropped']} dropped, "
            f"{opp_stats['missing']} .opp missing; {opp_stats['repaired_hops']} hops repaired "
            f"({opp_stats['inserted']} junctions inserted), {opp_stats['far_snaps']} far snaps")

    return names["blitz"], names["race"], names["circuit"], waypoint_counts
