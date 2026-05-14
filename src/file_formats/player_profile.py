"""
Player profile (.sav / .dir) reader/writer.
Mirrors mmPlayerData/mmPlayerDirectory (Open1560 mmcityinfo/playerdata.cpp, playerdir.cpp).

CRC: custom CRC-32, polynomial 0xED7282A0 (NOT standard zlib), init/final XOR 0xFFFFFFFF.

.sav layout:
  i32 Type=1  u32 CRC(217 bytes)
  i32 Progress  i8 Difficulty  char LastCarPicked[80]
  i32 LastCarColor  i32 LastGamePicked  i32 LastRacePicked
  char PlayerName[40]  char NetName[40]  char FileName[40]
  i32 count=12  + 12x mmPlayerRecord  (Checkpoint, Circuit, Blitz)

mmPlayerRecord (96 bytes):  u32 CRC  f32 Time  char CarName[80]  i32 Passed  i32 Score

.dir layout:
  i32 Type=4  i32 NumPlayers  N x (PlayerName[40] + FileName[40])  char LastPlayer[80]
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from pathlib import Path
from typing import BinaryIO, List, Optional

from src.io.binary import read_unpack, write_pack, read_binary_name, write_binary_name, pack_bytes
from src.constants.misc import Encoding
from src.constants.modes import GameMode, Difficulty, GAME_MODE_NAMES
from src.constants.vehicles import PlayerCar


PLAYER_DATA_TYPE      = 1
PLAYER_DIRECTORY_TYPE = 4

NUM_RECORD_SLOTS   = 12
PLAYER_NAME_LEN    = 40
LAST_CAR_LEN       = 80
RECORD_CAR_LEN     = 80
LAST_PLAYER_LEN    = 80


# ---------------------------------------------------------------------------
# CRC -- custom polynomial extracted from game.asm sym_643A68
# ---------------------------------------------------------------------------

# The game uses reflected CRC-32 with polynomial 0xED7282A0.
# Table[128] = 0xED7282A0 confirms the polynomial (entry 128 = 0b10000000 always
# produces the polynomial after 8 right-shift iterations).
_CRC_POLY = 0xED7282A0

def _make_crc_table() -> list:
    t = []
    for i in range(256):
        c = i
        for _ in range(8):
            c = (c >> 1) ^ _CRC_POLY if (c & 1) else c >> 1
        t.append(c)
    return t

_CRC_TABLE = _make_crc_table()


def _crc(data: bytes) -> int:
    """CRC-32 matching the game's UpdateCrc (polynomial 0xED7282A0, init=0xFFFFFFFF)."""
    crc = 0xFFFFFFFF
    for b in data:
        crc = _CRC_TABLE[(b ^ crc) & 0xFF] ^ (crc >> 8)
    return (~crc) & 0xFFFFFFFF


def _encode_fixed(s: str, length: int) -> bytes:
    """Encode string as ASCII, zero-padded / truncated to exactly `length` bytes."""
    return s.encode(Encoding.ASCII, errors="replace")[:length].ljust(length, b"\0")


@dataclass
class PlayerRecord:
    """
    One race result slot.  Mirrors mmPlayerRecord (playerdata.h).

    Binary layout of the 96-byte on-disk block:
      u32  crc  -- covers the following 92 bytes
      f32  time
      char car_name[80]
      i32  passed
      i32  score

    Note: SaveBinary writes Passed *before* Score even though the struct
    declares Score before Passed -- we match that exact write order here.
    """

    time:     float = 0.0
    car_name: str   = ""
    score:    int   = 0
    passed:   int   = 0

    def _payload(self) -> bytes:
        return (
            pack_bytes("<f",  self.time)
            + _encode_fixed(self.car_name, RECORD_CAR_LEN)
            + pack_bytes("<i", self.passed)
            + pack_bytes("<i", self.score)
        )

    def write(self, f: BinaryIO) -> None:
        payload = self._payload()
        write_pack(f, "<I", _crc(payload))
        f.write(payload)

    @classmethod
    def read(cls, f: BinaryIO) -> "PlayerRecord":
        stored_crc, = read_unpack(f, "<I")
        payload = f.read(4 + RECORD_CAR_LEN + 4 + 4)   # 92 bytes

        computed = _crc(payload)
        if computed != stored_crc:
            print(f"\t[WARN] PlayerRecord CRC mismatch "
                  f"(stored={stored_crc:#010x}, computed={computed:#010x})")

        buf = io.BytesIO(payload)
        def rf(): return read_unpack(buf, "<f")[0]
        def ri(): return read_unpack(buf, "<i")[0]

        time    = rf()
        car_raw = buf.read(RECORD_CAR_LEN)
        passed  = ri()
        score   = ri()

        null     = car_raw.find(b"\0")
        car_name = car_raw[:null if null >= 0 else None].decode(Encoding.ASCII, errors="replace")

        return cls(time=time, car_name=car_name, score=score, passed=passed)

    def is_empty(self) -> bool:
        return self.time == 0.0 and self.score == 0 and self.passed == 0

    def __repr__(self) -> str:
        if self.is_empty():
            return "(empty)"
        passed_str = "yes" if self.passed else "no"
        return (f"time={self.time:.2f}s  car={self.car_name!r}  "
                f"score={self.score}  passed={passed_str}")


@dataclass
class PlayerData:
    """
    Single player profile -- one .sav file.  Mirrors mmPlayerData (playerdata.h).
    """

    player_name:     str = "Player"
    net_name:        str = ""
    file_name:       str = "player0"

    difficulty:      int = Difficulty.PROFESSIONAL
    progress:        int = 7

    last_car_picked:  str = PlayerCar.PANOZ_GTR1
    last_car_color:   int = 0
    last_game_picked: int = GameMode.CHECKPOINT
    last_race_picked: int = 0

    checkpoint_records: List[PlayerRecord] = field(default_factory=list)
    circuit_records:    List[PlayerRecord] = field(default_factory=list)
    blitz_records:      List[PlayerRecord] = field(default_factory=list)

    def __post_init__(self) -> None:
        for bucket in (self.checkpoint_records, self.circuit_records, self.blitz_records):
            while len(bucket) < NUM_RECORD_SLOTS:
                bucket.append(PlayerRecord())
            if len(bucket) > NUM_RECORD_SLOTS:
                raise ValueError(f"At most {NUM_RECORD_SLOTS} records per category, got {len(bucket)}")

    def _header_payload(self) -> bytes:
        """217 bytes covered by the file-level CRC."""
        return (
            pack_bytes("<i",  self.progress)
            + pack_bytes("<b", self.difficulty)
            + _encode_fixed(self.last_car_picked, LAST_CAR_LEN)
            + pack_bytes("<i", self.last_car_color)
            + pack_bytes("<i", self.last_game_picked)
            + pack_bytes("<i", self.last_race_picked)
            + _encode_fixed(self.player_name, PLAYER_NAME_LEN)
            + _encode_fixed(self.net_name,    PLAYER_NAME_LEN)
            + _encode_fixed(self.file_name,   PLAYER_NAME_LEN)
        )

    def write(self, output_file: Path) -> None:
        header = self._header_payload()
        crc    = _crc(header)

        with open(output_file, "wb") as f:
            write_pack(f, "<i", PLAYER_DATA_TYPE)
            write_pack(f, "<I", crc)
            f.write(header)

            for bucket in (self.checkpoint_records, self.circuit_records, self.blitz_records):
                write_pack(f, "<i", NUM_RECORD_SLOTS)
                for record in bucket:
                    record.write(f)

    @classmethod
    def read(cls, path: Path) -> "PlayerData":
        _HEADER_LEN = 4 + 1 + LAST_CAR_LEN + 4 + 4 + 4 + PLAYER_NAME_LEN * 3  # 217

        with open(path, "rb") as f:
            file_type, = read_unpack(f, "<i")
            if file_type != PLAYER_DATA_TYPE:
                raise ValueError(f"Not a player .sav file (type={file_type})")

            stored_crc, = read_unpack(f, "<I")
            header      = f.read(_HEADER_LEN)

            computed = _crc(header)
            if computed != stored_crc:
                print(f"\t[WARN] PlayerData header CRC mismatch "
                      f"(stored={stored_crc:#010x}, computed={computed:#010x})")

            buf = io.BytesIO(header)
            def ri(): return read_unpack(buf, "<i")[0]
            def rb(): return read_unpack(buf, "<b")[0]

            progress         = ri()
            difficulty       = rb()
            last_car_raw     = buf.read(LAST_CAR_LEN)
            last_car_color   = ri()
            last_game_picked = ri()
            last_race_picked = ri()
            player_name_raw  = buf.read(PLAYER_NAME_LEN)
            net_name_raw     = buf.read(PLAYER_NAME_LEN)
            file_name_raw    = buf.read(PLAYER_NAME_LEN)

            def _str(b: bytes) -> str:
                pos = b.find(b"\0")
                return b[:pos if pos >= 0 else None].decode(Encoding.ASCII, errors="replace")

            def _read_bucket() -> List[PlayerRecord]:
                count, = read_unpack(f, "<i")
                return [PlayerRecord.read(f) for _ in range(count)]

            return cls(
                player_name      = _str(player_name_raw),
                net_name         = _str(net_name_raw),
                file_name        = _str(file_name_raw),
                difficulty       = difficulty,
                progress         = progress,
                last_car_picked  = _str(last_car_raw),
                last_car_color   = last_car_color,
                last_game_picked = last_game_picked,
                last_race_picked = last_race_picked,
                checkpoint_records = _read_bucket(),
                circuit_records    = _read_bucket(),
                blitz_records      = _read_bucket(),
            )

    def to_text(self, file_size: Optional[int] = None) -> str:
        lines: List[str] = []
        w = lambda s="": lines.append(s + "\n")

        diff_str = "Professional" if self.difficulty == Difficulty.PROFESSIONAL else "Amateur"
        mode_str = GAME_MODE_NAMES.get(self.last_game_picked, str(self.last_game_picked))
        total    = sum(r.score for r in
                       self.checkpoint_records + self.circuit_records + self.blitz_records
                       if r.passed)

        if file_size is not None:
            w(f"  file_size    : {file_size} bytes  (expected 3693)")
        w( "  Type         : 1  (PLAYER_DATA_TYPE)")
        w( "  CRC          : custom poly 0xED7282A0")
        w()
        w( "  -- Identity --")
        w(f"  player_name  : {self.player_name!r}")
        w(f"  net_name     : {self.net_name!r}  (multiplayer display name)")
        w(f"  file_name    : {self.file_name!r}  -> {self.file_name}.sav / {self.file_name}.cfg")
        w()
        w( "  -- Player state --")
        w(f"  difficulty   : {self.difficulty}  ({diff_str})")
        w(f"  progress     : {self.progress:#06x}  =  {self.progress:012b}b")
        w(f"  last_car     : {self.last_car_picked!r}  color index={self.last_car_color}")
        w(f"  last_game    : {self.last_game_picked}  ({mode_str})  <- mode shown on next launch")
        w(f"  last_race    : index {self.last_race_picked}  (within that mode)")
        w()
        w( "  -- Score summary --")
        w(f"  total passed score : {total}  (sum of all passed-race scores across all modes)")

        for label, bucket in (
            ("Checkpoint records", self.checkpoint_records),
            ("Circuit records",    self.circuit_records),
            ("Blitz records",      self.blitz_records),
        ):
            filled = [(i, r) for i, r in enumerate(bucket) if not r.is_empty()]
            w()
            w(f"  -- {label}  ({len(filled)}/12 slots filled) --")
            if filled:
                w(f"\t{'slot':>4}  {'time':>9}  {'car':<22}  {'score':>6}  passed  record_crc")
                w(f"\t{'----':>4}  {'--------':>9}  {'-'*22:<22}  {'-----':>6}  ------  ----------")
                for i, r in filled:
                    crc_val = _crc(r._payload())
                    ps = "YES" if r.passed else "no"
                    w(f"\t[{i:2d}]  {r.time:8.2f}s  {r.car_name:<22}  {r.score:6d}  {ps:<6}  {crc_val:#010x}")
            else:
                w("\t(all 12 slots empty -- no races completed)")

        return "".join(lines)

    @classmethod
    def debug_file(cls, input_file: Path, output_file: Path, enabled: bool) -> None:
        if not enabled:
            return
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        data = cls.read(input_file)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(data.to_text(file_size=input_file.stat().st_size))

        print(f"\tDebugged {input_file.name} -> {output_file.name}")


@dataclass
class PlayerDirectory:
    """
    Index file (`players.dir`).  Mirrors mmPlayerDirectory (playerdir.h).
    """

    entries:     List[tuple] = field(default_factory=list)   # [(player_name, file_name), ...]
    last_player: str         = ""

    def write(self, output_file: Path) -> None:
        with open(output_file, "wb") as f:
            write_pack(f, "<i", PLAYER_DIRECTORY_TYPE)
            write_pack(f, "<i", len(self.entries))
            for player_name, file_name in self.entries:
                write_binary_name(f, player_name, length=PLAYER_NAME_LEN)
                write_binary_name(f, file_name,   length=PLAYER_NAME_LEN)
            write_binary_name(f, self.last_player, length=LAST_PLAYER_LEN)

    @classmethod
    def read(cls, path: Path) -> "PlayerDirectory":
        with open(path, "rb") as f:
            file_type, = read_unpack(f, "<i")
            if file_type != PLAYER_DIRECTORY_TYPE:
                raise ValueError(f"Not a players.dir file (type={file_type})")

            count, = read_unpack(f, "<i")
            entries = []
            for _ in range(count):
                player_name = read_binary_name(f, PLAYER_NAME_LEN)
                file_name   = read_binary_name(f, PLAYER_NAME_LEN)
                entries.append((player_name, file_name))

            last_player = read_binary_name(f, LAST_PLAYER_LEN)

        return cls(entries=entries, last_player=last_player)

    def to_text(self, file_size: Optional[int] = None) -> str:
        lines: List[str] = []
        w = lambda s="": lines.append(s + "\n")

        if file_size is not None:
            w(f"  file_size   : {file_size} bytes")
        w( "\tType        : 4  (PLAYER_DIRECTORY_TYPE)")
        w(f"\tNumPlayers  : {len(self.entries)}")
        w(f"\tLastPlayer  : {self.last_player!r}  <- auto-selected on boot")
        w()
        w( "  Entries:")
        for i, (pn, fn) in enumerate(self.entries):
            w(f"\t[{i}]  PlayerName={pn!r}   FileName={fn!r}  -> {fn}.sav / {fn}.cfg")

        return "".join(lines)

    @classmethod
    def debug_file(cls, input_file: Path, output_file: Path, enabled: bool) -> None:
        if not enabled:
            return
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        data = cls.read(input_file)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(data.to_text(file_size=input_file.stat().st_size))

        print(f"\tDebugged {input_file.name} -> {output_file.name}")


def write_player_profile(
    output_folder:       Path,
    profile:             PlayerData,
    *,
    config:              Optional[object]             = None,
    make_default:        bool                         = True,
    additional_profiles: Optional[List[PlayerData]]  = None,
    additional_configs:  Optional[List[object]]       = None,
) -> None:
    """
    Write a .sav (+ optional .cfg) for each profile plus a matching players.dir.

    Parameters
    ----------
    output_folder
        Target directory; typically MidtownMadness/dev/players/.
    profile
        Primary profile.
    config
        Optional PlayerConfig for the primary profile.  When supplied a matching
        <file_name>.cfg is written alongside the .sav.
    make_default
        If True, players.dir's LastPlayer auto-selects this profile on boot.
    additional_profiles
        Extra profiles; each needs a unique file_name.
    additional_configs
        Configs for extra_profiles (positional match).  May be shorter than
        additional_profiles; unmatched profiles get no .cfg written.
    """
    output_folder.mkdir(parents=True, exist_ok=True)

    profiles = [profile] + (additional_profiles or [])
    configs  = ([config] if config else [None]) + list(additional_configs or [])
    # pad configs list so zip always has a pair
    while len(configs) < len(profiles):
        configs.append(None)

    seen: set = set()
    for p in profiles:
        if p.file_name in seen:
            raise ValueError(f"Duplicate file_name in profiles: {p.file_name!r}")
        seen.add(p.file_name)

    for p, cfg in zip(profiles, configs):
        sav_path = output_folder / f"{p.file_name}.sav"
        p.write(sav_path)
        print(f"\tWrote player save     ->  {sav_path.name}")

        if cfg is not None:
            cfg_path = output_folder / f"{p.file_name}.cfg"
            cfg.write(cfg_path)
            print(f"\tWrote player config   ->  {cfg_path.name}")

    directory = PlayerDirectory(
        entries     = [(p.player_name, p.file_name) for p in profiles],
        last_player = profile.player_name if make_default else "",
    )
    dir_path = output_folder / "players.dir"
    directory.write(dir_path)
    print(f"\tWrote player directory ->  {dir_path.name}  ({len(profiles)} profile(s))")