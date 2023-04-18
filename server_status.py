import socket
import time


def check(host, port, timeout=2):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # presumably
    sock.settimeout(timeout)
    try:
        sock.connect((host, port))
    except:  # noqa: E722
        return False
    else:
        sock.close()
        return True


def check_login_server():
    if not check("51.75.147.219", 3724, timeout=2):
        return False
    time.sleep(5)
    return check("51.75.147.219", 3724, timeout=2)


def check_game_server():
    if not check("51.75.147.219", 8086, timeout=2):
        return False
    time.sleep(5)
    return check("51.75.147.219", 8086, timeout=2)


def check_file_server():
    if not check("65.21.152.13", 443, timeout=2):
        return False
    time.sleep(5)
    return check("65.21.152.13", 443, timeout=2)
