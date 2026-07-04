import os
import platform
from pathlib import Path

__all__ = ["get_app_data_dir"]


def _get_windows_data() -> Path:
    """
    Returns the base directory for user-local application data on Windows.

    Uses the LOCALAPPDATA environment variable.

    Raises:
        ValueError: If LOCALAPPDATA is not set.
    """
    value: str | None = os.getenv("LOCALAPPDATA")
    if not value:
        raise ValueError("LOCALAPPDATA is not set")
    return Path(value)


def _get_macos_data() -> Path:
    """
    Returns the base directory for user-local application data on macOS.

    Typically: ~/Library/Application Support
    """
    return Path.home() / "Library" / "Application Support"


def _get_linux_data() -> Path:
    """
    Returns the base directory for user-local application data on Linux/BSD.

    Uses $XDG_DATA_HOME if set, otherwise falls back to ~/.local/share
    """
    xdg: str | None = os.getenv("XDG_DATA_HOME")
    if xdg:
        return Path(xdg)
    else:
        return Path.home() / ".local" / "share"


def get_app_data_dir() -> Path:
    """
    Returns the PassMan root directory for storing user data.

    Cross-platform paths:
    - Windows: %LOCALAPPDATA%\\.passman
    - macOS: ~/Library/Application Support/.passman
    - Linux/BSD: $XDG_DATA_HOME/.passman or ~/.local/share/.passman

    Returns:
        Path: Path to PassMan app data directory
    """
    if platform.system() == "Windows":
        DB_DIR = _get_windows_data() / ".passman"
    elif platform.system() == "Darwin":
        DB_DIR = _get_macos_data() / ".passman"
    else:
        DB_DIR = _get_linux_data() / ".passman"

    DB_DIR.mkdir(parents=True, exist_ok=True)

    return DB_DIR
