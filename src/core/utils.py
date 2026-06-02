import socket
import threading

_LOCK_PORT   = 47893
_lock_socket = None
_reload_event = threading.Event()

def acquire_instance_lock() -> bool:
    global _lock_socket
    try:
        _lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _lock_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
        _lock_socket.bind(("127.0.0.1", _LOCK_PORT))
        return True
    except OSError:
        return False

def get_reload_event() -> threading.Event:
    return _reload_event
