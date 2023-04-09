import ctypes
import logging
import time
from ctypes import wintypes

import keyring
from keyring.backends import Windows

keyring.set_keyring(Windows.WinVaultKeyring())


logging.basicConfig(
    filename="launcher.log",
    filemode="a",
    format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO,
)

logger = logging.getLogger("Password")

user32 = ctypes.WinDLL("user32", use_last_error=True)

INPUT_MOUSE = 0
INPUT_KEYBOARD = 1
INPUT_HARDWARE = 2

KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_SCANCODE = 0x0008

MAPVK_VK_TO_VSC = 0

# msdn.microsoft.com/en-us/library/dd375731
VK_TAB = 0x09
VK_MENU = 0x12
VK_SHIFT = 0x10  # SHIFT key
# C struct definitions

KEYS = {
    "1": 0x31,
    "2": 0x32,
    "3": 0x33,
    "4": 0x34,
    "5": 0x35,
    "6": 0x36,
    "7": 0x37,
    "8": 0x38,
    "9": 0x39,
    "A": 0x41,
    "B": 0x42,
    "C": 0x43,
    "D": 0x44,
    "E": 0x45,
    "F": 0x46,
    "G": 0x47,
    "H": 0x48,
    "I": 0x49,
    "J": 0x4A,
    "K": 0x4B,
    "L": 0x4C,
    "M": 0x4D,
    "N": 0x4E,
    "O": 0x4F,
    "P": 0x50,
    "Q": 0x51,
    "R": 0x52,
    "S": 0x53,
    "T": 0x54,
    "U": 0x55,
    "V": 0x56,
    "W": 0x57,
    "X": 0x58,
    "Y": 0x59,
    "Z": 0x5A,
    "+": 0xBB,
    ",": 0xBC,
    "-": 0xBD,
    ".": 0xBE,
    "ENTER": 0x0D,
}


wintypes.ULONG_PTR = wintypes.WPARAM


class MOUSEINPUT(ctypes.Structure):
    _fields_ = (
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", wintypes.ULONG_PTR),
    )


class KEYBDINPUT(ctypes.Structure):
    _fields_ = (
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", wintypes.ULONG_PTR),
    )

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
        # some programs use the scan code even if KEYEVENTF_SCANCODE
        # isn't set in dwFflags, so attempt to map the correct code.
        if not self.dwFlags & KEYEVENTF_UNICODE:
            self.wScan = user32.MapVirtualKeyExW(self.wVk, MAPVK_VK_TO_VSC, 0)


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = (
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    )


class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = (("ki", KEYBDINPUT), ("mi", MOUSEINPUT), ("hi", HARDWAREINPUT))

    _anonymous_ = ("_input",)
    _fields_ = (("type", wintypes.DWORD), ("_input", _INPUT))


LPINPUT = ctypes.POINTER(INPUT)


def _check_count(result, func, args):
    if result == 0:
        raise ctypes.WinError(ctypes.get_last_error())
    return args


user32.SendInput.errcheck = _check_count
user32.SendInput.argtypes = (
    wintypes.UINT,  # nInputs
    LPINPUT,  # pInputs
    ctypes.c_int,
)  # cbSize


def press_key(hexKeyCode):
    x = INPUT(type=INPUT_KEYBOARD, ki=KEYBDINPUT(wVk=hexKeyCode))
    user32.SendInput(1, ctypes.byref(x), ctypes.sizeof(x))


def release_key(hexKeyCode):
    x = INPUT(
        type=INPUT_KEYBOARD, ki=KEYBDINPUT(wVk=hexKeyCode, dwFlags=KEYEVENTF_KEYUP)
    )
    user32.SendInput(1, ctypes.byref(x), ctypes.sizeof(x))


def type_key(hexKeyCode):
    press_key(hexKeyCode)
    release_key(hexKeyCode)


def set_account_name(username):
    keyring.set_password("duskhaven_launcher", "account_name", username)


def get_account_name():
    return keyring.get_password("duskhaven_launcher", "account_name")


def delete_account_name():
    try:
        keyring.delete_password("duskhaven_launcher", "account_name")
        return True
    except keyring.errors.PasswordDeleteError:
        return False


def set_password(password):
    keyring.set_password("duskhaven_launcher", "password", password)


def get_password():
    return keyring.get_password("duskhaven_launcher", "password")


def delete_password():
    try:
        keyring.delete_password("duskhaven_launcher", "password")
        return True
    except keyring.errors.PasswordDeleteError:
        return False


def update_account_name(filename, new_account_name):
    with open(filename) as file:
        lines = file.readlines()
    # Look for the line that starts with "SET accountName"
    for i, line in enumerate(lines):
        if line.startswith("SET accountName"):
            # Replace the line with the new account name
            lines[i] = f'SET accountName "{new_account_name}"\n'
            break
    else:
        # If the line doesn't exist, add it to the end of the file
        lines.append(f'SET accountName "{new_account_name}"\n')
    with open(filename, "w") as file:
        file.writelines(lines)


def key_to_hex(name):
    return KEYS[name]


def type_password(password):
    for ch in password:
        try:
            if ch.isupper():
                press_key(VK_SHIFT)
                type_key(KEYS[ch.upper()])
                release_key(VK_SHIFT)
            elif ch == "_":
                press_key(VK_SHIFT)
                type_key(KEYS["-"])
                release_key(VK_SHIFT)
            else:
                press_key(KEYS[ch.upper()])
                release_key(KEYS[ch.upper()])
        except Exception:
            logger.error("Cannot parse password")
        time.sleep(0.05)
