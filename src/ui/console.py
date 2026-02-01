YELLOW = "\033[93m"
GREEN = "\033[92m"
RED = "\033[91m"
CYAN = "\033[96m"
RESET = "\033[0m"


def yellow(msg: str) -> str:
    return f"{YELLOW}{msg}{RESET}"


def green(msg: str) -> str:
    return f"{GREEN}{msg}{RESET}"


def red(msg: str) -> str:
    return f"{RED}{msg}{RESET}"


def cyan(msg: str) -> str:
    return f"{CYAN}{msg}{RESET}"