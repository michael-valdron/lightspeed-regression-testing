#!/usr/bin/env python3
"""Wait for Lightspeed Core readiness, then exec the container command (pytest)."""

from __future__ import annotations

import os
import sys
import time

import requests


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw.strip())
    except ValueError:
        print(
            f"entrypoint: {name}={raw!r} is not an integer; using default {default}",
            file=sys.stderr,
        )
        return default


def _skip_wait() -> bool:
    raw = os.getenv("SKIP_READINESS_WAIT")
    return raw is not None and bool(raw.strip())


def wait_for_readiness() -> None:
    if _skip_wait():
        print("entrypoint: SKIP_READINESS_WAIT set; skipping readiness poll")
        return

    base_url = os.getenv("LS_BASE_URL", "http://localhost:8080").rstrip("/")
    readiness_url = f"{base_url}/readiness"
    timeout_seconds = _env_int("READINESS_TIMEOUT_SECONDS", 300)
    interval_seconds = _env_int("READINESS_INTERVAL_SECONDS", 5)
    grace_seconds = _env_int("READINESS_GRACE_SECONDS", 0)

    print(f"entrypoint: waiting for {readiness_url} (timeout={timeout_seconds}s)")
    deadline = time.monotonic() + timeout_seconds
    last_error: str | None = None

    while time.monotonic() < deadline:
        try:
            response = requests.get(readiness_url, timeout=min(interval_seconds, 10))
            if response.ok:
                print(f"entrypoint: readiness OK (HTTP {response.status_code})")
                if grace_seconds > 0:
                    print(f"entrypoint: grace sleep {grace_seconds}s")
                    time.sleep(grace_seconds)
                return
            last_error = f"HTTP {response.status_code}"
        except requests.RequestException as exc:
            last_error = str(exc)

        print(f"entrypoint: not ready ({last_error}); retrying in {interval_seconds}s")
        time.sleep(interval_seconds)

    print(
        f"entrypoint: timed out after {timeout_seconds}s waiting for {readiness_url}"
        + (f" (last error: {last_error})" if last_error else ""),
        file=sys.stderr,
    )
    sys.exit(1)


def main() -> None:
    wait_for_readiness()
    command = sys.argv[1:]
    if not command:
        print("entrypoint: no command provided", file=sys.stderr)
        sys.exit(1)
    os.execvp(command[0], command)


if __name__ == "__main__":
    main()
