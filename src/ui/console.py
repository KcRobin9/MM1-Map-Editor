import io
import sys
from contextlib import contextmanager
from colorama import Fore, Style

# ── Inline color helpers ───────────────────────────────────────────────────────

def yellow(text: str) -> str:
    return f"{Fore.YELLOW}{text}{Style.RESET_ALL}"

def green(text: str) -> str:
    return f"{Fore.GREEN}{text}{Style.RESET_ALL}"

def red(text: str) -> str:
    return f"{Fore.RED}{text}{Style.RESET_ALL}"

def cyan(text: str) -> str:
    return f"{Fore.CYAN}{text}{Style.RESET_ALL}"

def magenta(text: str) -> str:
    return f"{Fore.MAGENTA}{text}{Style.RESET_ALL}"

def white(text: str) -> str:
    return f"{Fore.WHITE}{text}{Style.RESET_ALL}"

# ── Structured console output ──────────────────────────────────────────────────

LINE_WIDTH = 100  # max visual characters per line before wrapping

def ok(message: str) -> None:
    """Green checkmark success line."""
    print(f"{Fore.LIGHTGREEN_EX}✓{Style.RESET_ALL} {message}")

def sep() -> str:
    """Inline cyan · separator — use inside ok() to append secondary info."""
    return f"  {Fore.CYAN}·{Style.RESET_ALL}  "

def detail(label: str, value: str, col: int = 0) -> None:
    """Indented labeled detail row, word-wrapped at LINE_WIDTH.
    col: minimum label column width — pass max(len(l) for l in labels) to align a group."""
    padded       = label.ljust(col)
    prefix_plain = f"  · {padded}  "
    prefix       = f"  {Fore.CYAN}·{Style.RESET_ALL} {padded}  "
    _wrapped(prefix, len(prefix_plain), value)

def item(value: str) -> None:
    """Indented unlabeled detail row, word-wrapped at LINE_WIDTH."""
    prefix_plain = "  · "
    prefix       = f"  {Fore.CYAN}·{Style.RESET_ALL} "
    _wrapped(prefix, len(prefix_plain), value)

def _wrapped(prefix: str, prefix_len: int, text: str) -> None:
    first_avail = LINE_WIDTH - prefix_len
    indent      = " " * prefix_len
    rest_avail  = LINE_WIDTH - prefix_len

    parts                         = text.split(", ")
    lines, current, current_len   = [], [], 0
    avail                         = first_avail

    for part in parts:
        segment_len = len(part) + (2 if current else 0)
        if current_len + segment_len > avail and current:
            lines.append(", ".join(current))
            current, current_len, avail = [part], len(part), rest_avail
        else:
            current.append(part)
            current_len += segment_len

    if current:
        lines.append(", ".join(current))

    for i, line in enumerate(lines):
        print(f"{prefix if i == 0 else indent}{line}")


@contextmanager
def suppress_stdout_matching(substring: str):
    """Context manager that swallows stdout lines containing `substring`."""
    class _Filter(io.TextIOBase):
        def __init__(self, real):
            self._real = real
            self._buf  = ""

        def write(self, s: str) -> int:
            self._buf += s
            while "\n" in self._buf:
                line, self._buf = self._buf.split("\n", 1)
                if substring not in line:
                    self._real.write(line + "\n")
            return len(s)

        def flush(self):
            if self._buf:
                if substring not in self._buf:
                    self._real.write(self._buf)
                self._buf = ""
            self._real.flush()

    old = sys.stdout
    sys.stdout = _Filter(old)
    try:
        yield
    finally:
        sys.stdout.flush()
        sys.stdout = old
