"""
Midtown Madness Map Editor - Settings GUI
==========================================
A local web-based GUI for editing all four settings files.

Usage:
    python settings_gui.py
    python settings_gui.py --port 8585

Then open http://localhost:8585 in your browser.
The tool auto-detects the settings files relative to the project root.

Copyright (C) 2025 Robin - Part of the Midtown Madness 1 Map Editor
"""

import os
import re
import sys
import json
import shutil
import signal
import hashlib
import argparse
import webbrowser
import threading
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler

# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent


def find_project_root():
    """Walk upward from this script to find the project root."""
    candidate = SCRIPT_DIR
    for _ in range(6):
        if (candidate / "src" / "USER" / "settings").is_dir():
            return candidate
        candidate = candidate.parent
    return SCRIPT_DIR


PROJECT_ROOT = find_project_root()

SETTINGS_FILES = {
    "main":     PROJECT_ROOT / "src" / "USER" / "settings" / "main.py",
    "advanced": PROJECT_ROOT / "src" / "USER" / "settings" / "advanced.py",
    "debug":    PROJECT_ROOT / "src" / "USER" / "settings" / "debug.py",
    "blender":  PROJECT_ROOT / "src" / "USER" / "settings" / "blender.py",
}

BACKUP_DIR = PROJECT_ROOT / "src" / "USER" / "settings" / ".backups"

# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

# Build the regex pattern in parts to avoid any escaping issues.
# Captures: indent, varname, value, comment
_RE_PARTS = [
    r'^',
    r'(?P<indent>\s*)',           # leading whitespace
    r'(?P<varname>[A-Za-z_]\w*)', # variable name
    r'\s*=\s*',                   # equals sign
    r'(?P<value>.+?)',            # value (non-greedy)
    r'(?:\s*#[!?*]?\s*',         # optional comment marker (handles #, #!, #?, #*)
    r'(?P<comment>.*))?',         # comment text
    r'$',
]
ASSIGN_RE = re.compile("".join(_RE_PARTS))

TUPLE_RE = re.compile(r'^\(.*\)$')
LIST_RE = re.compile(r'^\[.*\]$')
FOLDER_PATH_RE = re.compile(r'^Folder\.')
TEXTURE_RE = re.compile(r'^Texture\.')


def classify_value(raw):
    """Return (python_value, value_type) for a raw string from a .py file."""
    stripped = raw.strip().rstrip(",")

    if stripped in ("True", "False"):
        return stripped == "True", "bool"

    if stripped == "None":
        return None, "none"

    # Quoted strings
    if (stripped.startswith('"') and stripped.endswith('"')) or \
       (stripped.startswith("'") and stripped.endswith("'")):
        return stripped[1:-1], "str"

    # Integer
    try:
        return int(stripped), "int"
    except ValueError:
        pass

    # Float
    try:
        return float(stripped), "float"
    except ValueError:
        pass

    # Tuple of numbers  e.g. (40.0, 30.0, -40.0)
    if TUPLE_RE.match(stripped):
        return stripped, "tuple"

    # List
    if LIST_RE.match(stripped):
        return stripped, "list"

    # Folder / Path references - treat as read-only expressions
    if FOLDER_PATH_RE.match(stripped) or "/" in stripped:
        return stripped, "path"

    # Texture references
    if TEXTURE_RE.match(stripped):
        return stripped, "texture"

    # Anything else (complex expression) - read-only
    return stripped, "expr"


def parse_settings_file(path):
    """
    Parse a settings .py file into a list of entries.
    Each entry is either a variable dict or a raw-line dict.
    Preserves ordering so we can reconstruct the file exactly.
    """
    entries = []
    if not path.exists():
        return entries

    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for lineno, line in enumerate(lines, start=1):
        raw = line.rstrip("\n")

        lstripped = raw.lstrip()
        is_skip = (
            lstripped.startswith("#")
            or lstripped.startswith("from ")
            or lstripped.startswith("import ")
        )

        m = ASSIGN_RE.match(raw)
        if m and not is_skip:
            vname = m.group("varname")
            value_raw = m.group("value").strip()
            comment = (m.group("comment") or "").strip()
            indent = m.group("indent")

            value, vtype = classify_value(value_raw)

            entries.append({
                "kind": "var",
                "lineno": lineno,
                "indent": indent,
                "name": vname,
                "value": value,
                "value_raw": value_raw,
                "value_type": vtype,
                "comment": comment,
                "raw": raw,
            })
        else:
            entries.append({
                "kind": "line",
                "lineno": lineno,
                "raw": raw,
            })

    return entries


def reconstruct_file(entries):
    """Rebuild the .py file text from entries (preserving non-variable lines exactly)."""
    lines = []
    for entry in entries:
        if entry["kind"] == "line":
            lines.append(entry["raw"])
        else:
            indent = entry.get("indent", "")
            name = entry["name"]
            value_raw = entry["value_raw"]
            comment = entry.get("comment", "")

            base = indent + name + " = " + value_raw
            if comment:
                pad = max(1, 40 - len(base))
                lines.append(base + (" " * pad) + "# " + comment)
            else:
                lines.append(base)

    return "\n".join(lines) + "\n"


def python_repr(value, vtype):
    """Convert a JSON-decoded value back to valid Python source text."""
    if vtype == "bool":
        return "True" if value else "False"
    if vtype == "none":
        return "None"
    if vtype == "str":
        return '"' + str(value) + '"'
    if vtype == "int":
        return str(int(value))
    if vtype == "float":
        return str(value)
    if vtype in ("tuple", "list", "path", "texture", "expr"):
        return str(value)
    return str(value)


# ---------------------------------------------------------------------------
# Backup helpers
# ---------------------------------------------------------------------------

def create_backup(file_key, path):
    """Create a timestamped backup. Returns backup filename or None."""
    if not path.exists():
        return None
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = file_key + "_" + ts + ".py"
    shutil.copy2(path, BACKUP_DIR / backup_name)
    return backup_name


# ---------------------------------------------------------------------------
# API logic
# ---------------------------------------------------------------------------

def api_get_all():
    """Read all settings files and return structured data."""
    result = {}
    for key, path in SETTINGS_FILES.items():
        entries = parse_settings_file(path)
        variables = []
        for e in entries:
            if e["kind"] == "var":
                variables.append({
                    "name":       e["name"],
                    "value":      e["value"],
                    "value_raw":  e["value_raw"],
                    "value_type": e["value_type"],
                    "comment":    e["comment"],
                    "editable":   e["value_type"] in ("bool", "str", "int", "float", "none", "tuple"),
                })
        result[key] = {
            "path": str(path),
            "exists": path.exists(),
            "variables": variables,
        }
    return result


def api_save(file_key, changes):
    """
    Apply changes to a settings file.
    changes is a dict of {variable_name: new_value}.
    """
    if file_key not in SETTINGS_FILES:
        return {"ok": False, "error": "Unknown settings file: " + file_key}

    path = SETTINGS_FILES[file_key]
    if not path.exists():
        return {"ok": False, "error": "File not found: " + str(path)}

    entries = parse_settings_file(path)

    changed_count = 0
    for entry in entries:
        if entry["kind"] != "var":
            continue
        if entry["name"] in changes:
            new_val = changes[entry["name"]]
            vtype = entry["value_type"]

            new_raw = python_repr(new_val, vtype)
            if new_raw != entry["value_raw"]:
                entry["value_raw"] = new_raw
                entry["value"] = new_val
                changed_count += 1

    if changed_count == 0:
        return {"ok": True, "backup": None, "changed": 0}

    backup = create_backup(file_key, path)

    text = reconstruct_file(entries)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

    return {"ok": True, "backup": backup, "changed": changed_count}


def api_list_backups():
    """List all available backups."""
    if not BACKUP_DIR.exists():
        return []
    backups = sorted(BACKUP_DIR.glob("*.py"), key=lambda p: p.stat().st_mtime, reverse=True)
    return [{"name": b.name, "size": b.stat().st_size, "modified": b.stat().st_mtime} for b in backups]


def api_restore_backup(backup_name):
    """Restore a specific backup file."""
    backup_path = BACKUP_DIR / backup_name
    if not backup_path.exists():
        return {"ok": False, "error": "Backup not found: " + backup_name}

    file_key = None
    for key in SETTINGS_FILES:
        if backup_name.startswith(key + "_"):
            file_key = key
            break

    if file_key is None:
        return {"ok": False, "error": "Cannot determine target for backup: " + backup_name}

    target = SETTINGS_FILES[file_key]
    create_backup(file_key, target)
    shutil.copy2(backup_path, target)
    return {"ok": True, "restored": file_key}


# ---------------------------------------------------------------------------
# HTTP Server
# ---------------------------------------------------------------------------

HTML_PATH = SCRIPT_DIR / "settings_gui.html"


class SettingsHandler(SimpleHTTPRequestHandler):
    """Handle API requests and serve the HTML GUI."""

    def log_message(self, format, *args):
        pass

    def _send_json(self, data, status=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        return json.loads(raw) if raw else {}

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self._serve_html()
        elif self.path == "/api/settings":
            self._send_json(api_get_all())
        elif self.path == "/api/backups":
            self._send_json(api_list_backups())
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/api/save":
            body = self._read_body()
            file_key = body.get("file")
            changes = body.get("changes", {})
            result = api_save(file_key, changes)
            self._send_json(result)
        elif self.path == "/api/restore":
            body = self._read_body()
            result = api_restore_backup(body.get("backup", ""))
            self._send_json(result)
        else:
            self.send_error(404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _serve_html(self):
        if not HTML_PATH.exists():
            self.send_error(500, "settings_gui.html not found next to settings_gui.py")
            return
        with open(HTML_PATH, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run_server(port):
    server = HTTPServer(("127.0.0.1", port), SettingsHandler)
    url = "http://localhost:" + str(port)

    print("")
    print("  +---------------------------------------------+")
    print("  |   MM Map Editor - Settings GUI              |")
    print("  |   %-42s|" % url)
    print("  |                                             |")
    print("  |   Press Ctrl+C to stop                      |")
    print("  +---------------------------------------------+")
    print("")
    print("  Project root: " + str(PROJECT_ROOT))
    for key, path in SETTINGS_FILES.items():
        status = "ok" if path.exists() else "NOT FOUND"
        print("    %10s: %s" % (key, status))
    print()

    threading.Timer(0.8, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Shutting down...")
        server.shutdown()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Midtown Madness Map Editor - Settings GUI")
    parser.add_argument("--port", type=int, default=8585, help="Port to serve on (default: 8585)")
    parser.add_argument("--no-browser", action="store_true", help="Don't auto-open browser")
    args = parser.parse_args()

    if args.no_browser:
        webbrowser.open = lambda *a, **k: None

    run_server(args.port)