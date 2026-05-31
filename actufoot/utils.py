import time
from datetime import datetime


def _log_warn(msg: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [WARN] {msg}", flush=True)


def retry(fn, attempts: int = 3, delay: float = 5.0):
    """Tente fn() jusqu'à `attempts` fois. Lève la dernière exception si tout échoue."""
    last_exc = None
    for n in range(1, attempts + 1):
        try:
            return fn()
        except Exception as e:
            last_exc = e
            if n < attempts:
                _log_warn(f"tentative {n}/{attempts} échouée : {e}")
                time.sleep(delay)
    raise last_exc
