import struct
import psutil


def is_float(value: str) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False


def calc_size(fmt: str) -> int:
    return struct.calcsize(fmt)


def is_process_running(process_name: str) -> bool:
    for proc in psutil.process_iter(["name"]):
        if process_name.lower() in proc.info["name"].lower():
            return True
    return False