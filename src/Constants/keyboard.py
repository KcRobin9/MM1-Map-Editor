class Key:
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"
    H = "H"
    I = "I"
    J = "J"
    K = "K"
    L = "L"
    M = "M"
    N = "N"
    O = "O"
    P = "P"
    Q = "Q"
    R = "R"
    S = "S"
    T = "T"
    U = "U"
    V = "V"
    W = "W"
    X = "X"
    Y = "Y"
    Z = "Z"
    
    ZERO = "ZERO"
    ONE = "ONE"
    TWO = "TWO"
    THREE = "THREE"
    FOUR = "FOUR"
    FIVE = "FIVE"
    SIX = "SIX"
    SEVEN = "SEVEN"
    EIGHT = "EIGHT"
    NINE = "NINE"
    
    F1 = "F1"
    F2 = "F2"
    F3 = "F3"
    F4 = "F4"
    F5 = "F5"
    F6 = "F6"
    F7 = "F7"
    F8 = "F8"
    F9 = "F9"
    F10 = "F10"
    F11 = "F11"
    F12 = "F12"
    
    SPACE = "SPACE"
    TAB = "TAB"
    ENTER = "RET"
    ESC = "ESC"
    DELETE = "DEL"
    BACKSPACE = "BACK_SPACE"


class KeyEvent:
    PRESS = "PRESS"
    RELEASE = "RELEASE"
    CLICK = "CLICK"
    CLICK_DRAG = "CLICK_DRAG"


class KeyModifier:
    CTRL = {"ctrl": True}
    SHIFT = {"shift": True}
    ALT = {"alt": True}
    OSKEY = {"oskey": True}
    
    CTRL_SHIFT = {"ctrl": True, "shift": True}
    CTRL_ALT = {"ctrl": True, "alt": True}
    SHIFT_ALT = {"shift": True, "alt": True}
    CTRL_SHIFT_ALT = {"ctrl": True, "shift": True, "alt": True}