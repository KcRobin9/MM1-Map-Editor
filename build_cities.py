"""
Build one or more MM2 cities sequentially.

Usage:
  python build_cities.py              # build every configured city
  python build_cities.py SF BA        # build only SF and BA
  python build_cities.py SF           # build only SF

Each city writes its own .ar file (MM2SF.ar, MM2BA.ar, etc.) so they can coexist in
MidtownMadness/ --- load any of them in Open1560 by picking the race locale in-game.

Each build runs MAP_EDITOR_ALPHA_v1.py in a subprocess with the BUILD_CITY environment variable
set. That variable is read by src/USER/settings/local.py, which is git-ignored: multi-city builds
need a CITY_CFGS mapping there, so a fresh clone is told to set one up rather than silently
building the same map once per name.
"""
import os
import sys
import time
import subprocess
from typing import Dict, List, Tuple

from src.constants.mm2 import Mm2City
from src.constants.folder import Folder
from src.ui.console import item

DIVIDER = "=" * 70
CITY_ENV_VAR = "BUILD_CITY"


def configured_cities() -> List[str]:
    """City names this install can actually build, from settings/local.py's CITY_CFGS.

    Returns an empty list when no per-city config exists, which is the fresh-clone case.
    """
    try:
        from src.USER.settings.main import CITY_CFGS
    except ImportError:
        return []

    return [city for city in Mm2City.ALL if city in CITY_CFGS] + \
           [city for city in CITY_CFGS if city not in Mm2City.ALL]


def parse_cities(argv: List[str], available: List[str]) -> List[str]:
    """Command-line city names (upper-cased), or every configured city when none are given."""
    if not argv:
        return available

    cities = [city.upper() for city in argv]
    unknown = [city for city in cities if city not in available]
    if unknown:
        item(f"Unknown city name(s): {', '.join(unknown)}")
        item(f"Configured: {', '.join(available)}")
        sys.exit(1)

    return cities


def build_city(city: str, index: int, total: int) -> Tuple[bool, float]:
    print(f"\n{DIVIDER}")
    print(f"  Building {city}  ({index}/{total})")
    print(f"{DIVIDER}\n")

    environment = os.environ.copy()
    environment[CITY_ENV_VAR] = city

    started = time.time()
    result = subprocess.run([sys.executable, str(Folder.EDITOR_SCRIPT)],
                            env = environment, cwd = str(Folder.BASE))
    elapsed = time.time() - started

    succeeded = result.returncode == 0
    status = "OK" if succeeded else f"FAILED (exit {result.returncode})"
    print(f"\n  [{city}] {status} --- {elapsed:.0f}s\n")

    return succeeded, elapsed


def print_summary(results: Dict[str, Tuple[bool, float]], total_elapsed: float) -> None:
    print(f"\n{DIVIDER}")
    print("  Build summary:")

    for city, (succeeded, elapsed) in results.items():
        print(f"    {city:<8}  {'OK' if succeeded else 'FAILED'}  ({elapsed:.0f}s)")

    print(f"  Total: {total_elapsed:.0f}s")
    print(f"{DIVIDER}\n")


def main() -> None:
    available = configured_cities()
    if not available:
        raise SystemExit(
            "No per-city configuration found.\n"
            "Multi-city builds read CITY_CFGS from src/USER/settings/local.py (git-ignored), which\n"
            f"maps each city name to its MM2 source paths and keys off the {CITY_ENV_VAR} variable.\n"
            f"Without it every name would rebuild the same map. Expected names: "
            f"{', '.join(Mm2City.ALL)}")

    cities = parse_cities(sys.argv[1:], available)
    results: Dict[str, Tuple[bool, float]] = {}
    started = time.time()

    for index, city in enumerate(cities, start = 1):
        results[city] = build_city(city, index, len(cities))

    print_summary(results, time.time() - started)

    if not all(succeeded for succeeded, _ in results.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
