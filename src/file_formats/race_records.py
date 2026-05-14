"""
Race records (.dat) reader/writer for leaderboards.
One file per city per difficulty (amateur / pro).

Layout: i32 Type=1234  i32 MaxSlotsPerRace
  TotalRaces*MaxSlots x mmRecord (132 bytes: u32 CRC + Name[40] + CarName[80] + f32 Time + i32 Passed)
  Chicago: 30 races * 12 slots = 47536 bytes total (+ 8 pad)

Valid entry: CarName non-empty AND Time > 0 AND Passed in {0,1}
Mode ordering (Blitz/Circuit/Checkpoint) is assumed, may be Checkpoint-first.
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from src.file_formats.player_profile import _crc
from src.io.binary import write_pack, pack_bytes, read_unpack
from src.constants.misc import Encoding
from src.constants.modes import GameMode, GAME_MODE_NAMES


RECORD_SIZE    = 132   # bytes per mmRecord slot on disk
RECORD_CRC_LEN = 128   # bytes covered by CRC (after the 4-byte CRC field)

# Assumed ordering of modes in the .dat file for Chicago (30 races = 3 modes x 10 races).
# May be Checkpoint-first — not yet confirmed from source.
_DAT_MODE_ORDER = [GameMode.BLITZ, GameMode.CIRCUIT, GameMode.CHECKPOINT]


@dataclass
class RaceEntry:
    name:     str
    car_name: str
    time:     float
    passed:   int

    def is_valid(self) -> bool:
        return bool(self.car_name) and self.time > 0.0 and self.passed in (0, 1)


@dataclass
class RaceRecords:
    type_:          int
    slots_per_race: int
    total_races:    int
    entries: List[List[List[RaceEntry]]]  # [race_index][slot_index] -> RaceEntry

    def write(self, path: Path) -> None:
        """
        All races are written in order.  Each race gets exactly `slots_per_race`
        records.  Valid RaceEntry objects are written first (up to slots_per_race),
        then remaining slots are padded with empty (all-zero payload) records.
        """
        _EMPTY_PAYLOAD = bytes(RECORD_CRC_LEN)
        _EMPTY_CRC     = _crc(_EMPTY_PAYLOAD)

        def _write_record(f, entry: RaceEntry) -> None:
            name_b  = entry.name.encode(Encoding.ASCII, "replace")[:40].ljust(40, b"\x00")
            car_b   = entry.car_name.encode(Encoding.ASCII, "replace")[:80].ljust(80, b"\x00")
            payload = name_b + car_b + pack_bytes("<fi", entry.time, entry.passed)
            write_pack(f, "<I", _crc(payload))
            f.write(payload)

        def _write_empty(f) -> None:
            write_pack(f, "<I", _EMPTY_CRC)
            f.write(_EMPTY_PAYLOAD)

        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            write_pack(f, "<ii", self.type_, self.slots_per_race)
            for race_idx in range(self.total_races):
                if race_idx < len(self.entries):
                    valid = [e for slot in self.entries[race_idx] for e in slot if e.is_valid()]
                else:
                    valid = []
                written = 0
                for entry in valid[:self.slots_per_race]:
                    _write_record(f, entry)
                    written += 1
                for _ in range(self.slots_per_race - written):
                    _write_empty(f)
            # 8-byte trailing padding (matches original file)
            f.write(b"\x00" * 8)

    @classmethod
    def make_empty(cls, total_races: int = 30, slots_per_race: int = 12) -> "RaceRecords":
        """Create a blank leaderboard (all slots empty) with the given dimensions."""
        return cls(
            type_          = 1234,
            slots_per_race = slots_per_race,
            total_races    = total_races,
            entries        = [[] for _ in range(total_races)],
        )
    
    @classmethod
    def read(cls, path: Path) -> "RaceRecords":
        data = path.read_bytes()

        header = io.BytesIO(data[:8])
        type_          = read_unpack(header, "<i")[0]
        slots_per_race = read_unpack(header, "<i")[0]
        body           = data[8:]

        total_slots = len(body) // RECORD_SIZE
        total_races = total_slots // slots_per_race

        def _str(b: bytes) -> str:
            null = b.find(b"\x00")
            return b[:null if null >= 0 else None].decode(Encoding.ASCII, "replace")

        entries: List[List[List[RaceEntry]]] = []
        for race in range(total_races):
            race_slots: List[List[RaceEntry]] = []
            for slot in range(slots_per_race):
                off = (race * slots_per_race + slot) * RECORD_SIZE
                if off + RECORD_SIZE > len(body):
                    break

                # CRC[4] + Name[40] + CarName[80] + Time[4] + Passed[4] = 132 bytes
                rec     = io.BytesIO(body[off : off + RECORD_SIZE])
                rec.seek(4)  # skip stored CRC
                name_raw = rec.read(40)
                car_raw  = rec.read(80)
                time,    = read_unpack(rec, "<f")
                passed,  = read_unpack(rec, "<i")

                race_slots.append([RaceEntry(name=_str(name_raw), car_name=_str(car_raw),
                                             time=time, passed=passed)])
            entries.append(race_slots)

        return cls(
            type_          = type_,
            slots_per_race = slots_per_race,
            total_races    = total_races,
            entries        = entries,
        )

    def to_text(self, file_size: Optional[int] = None) -> str:
        lines: List[str] = []
        w = lambda s="": lines.append(s + "\n")

        races_per_mode = self.total_races // len(_DAT_MODE_ORDER)

        if file_size is not None:
            w(f"  file_size       : {file_size} bytes  (expected 47536 for Chicago)")
        w(f"  Type            : {self.type_}  (mmInfoBase::Type = 1234)")
        w(f"  MaxSlotsPerRace : {self.slots_per_race}")
        w(f"  TotalRaces      : {self.total_races}  ({races_per_mode} per mode x {len(_DAT_MODE_ORDER)} modes)")
        w(f"  RecordSize      : {RECORD_SIZE} bytes each")
        w( "  CRC algo        : custom poly 0xED7282A0 (same as .sav)")
        w( "  Filter          : car != '' AND time > 0 AND passed in {0,1}")
        w( "  NOTE            : mode ordering (Blitz/Circuit/Checkpoint) is assumed,")
        w( "                    not confirmed from source. May be Checkpoint-first.")

        for mode_i, mode_id in enumerate(_DAT_MODE_ORDER):
            mode_name = GAME_MODE_NAMES[mode_id]
            base = mode_i * races_per_mode
            w()
            w(f"  -- {mode_name}  (races {base}-{base + races_per_mode - 1}) --")
            any_entry = False

            for ri in range(races_per_mode):
                race     = base + ri
                if race >= len(self.entries):
                    break
                valid = [e for slot in self.entries[race] for e in slot if e.is_valid()]
                if not valid:
                    continue

                any_entry = True
                w(f"\tRace {ri:2d}  (global slot #{race}):")
                w(f"\t\t{'pos':>3}  {'player':<15}  {'car':<22}  {'time':>10}  passed")
                w(f"\t\t{'---':>3}  {'-'*15:<15}  {'-'*22:<22}  {'-'*10:>10}  ------")

                for idx, e in enumerate(valid):
                    mm = int(e.time // 60)
                    ss = e.time % 60
                    w(f"\t[{idx:2d}]  {e.name:<15}  {e.car_name:<22}  {mm}:{ss:05.2f}  {'YES' if e.passed else 'no'}")

            if not any_entry:
                w("  (no valid entries in this mode)")

        return "".join(lines)

    @classmethod
    def debug_file(cls, input_file: Path, output_file: Path, enabled: bool) -> None:
        if not enabled:
            return
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        records = cls.read(input_file)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(records.to_text(file_size=input_file.stat().st_size))

        print(f"\tDebugged {input_file.name} -> {output_file.name}")
