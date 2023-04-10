import logging
import sys
import time

import keyring
from pynput.keyboard import Controller

keyboard = Controller()

if sys.platform.startswith("win"):
    from keyring.backends import Windows

    keyring.set_keyring(Windows.WinVaultKeyring())
elif sys.platform.startswith("linux"):
    from keyring.backends import SecretService

    keyring.set_keyring(SecretService.Keyring())

logging.basicConfig(
    filename="launcher.log",
    filemode="a",
    format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO,
)

logger = logging.getLogger("Password")


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
        lines.append(f'SET accountName "{new_account_name}"\n')
    with open(filename, "w") as file:
        file.writelines(lines)


def type_key(key):
    keyboard.press(key)
    keyboard.release(key)


def type_password(password):
    for ch in password:
        keyboard.press(ch)
        keyboard.release(ch)
        time.sleep(0.05)
