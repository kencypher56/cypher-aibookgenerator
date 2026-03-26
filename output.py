"""
output.py
Format routing and Desktop path resolution for book output.
"""

import logging
import platform
import re
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Desktop path resolution
# ─────────────────────────────────────────────

def get_desktop_path() -> Path:
    """
    Return the Desktop directory path for the current OS.
    Falls back to home directory if Desktop cannot be resolved.
    """
    system = platform.system()

    if system == "Windows":
        # Prefer USERPROFILE env var; fall back to home
        import os
        user_profile = os.environ.get("USERPROFILE") or Path.home()
        desktop = Path(user_profile) / "Desktop"
    elif system == "Darwin":
        desktop = Path.home() / "Desktop"
    else:
        # Linux / other Unix
        # Respect XDG_DESKTOP_DIR if set
        import os
        xdg_desktop = os.environ.get("XDG_DESKTOP_DIR")
        if xdg_desktop and Path(xdg_desktop).exists():
            desktop = Path(xdg_desktop)
        else:
            desktop = Path.home() / "Desktop"

    # If Desktop doesn't exist, fall back to home directory
    if not desktop.exists():
        logger.warning(
            "Desktop path '%s' does not exist. Falling back to home directory.", desktop
        )
        desktop = Path.home()

    return desktop


def _safe_filename(title: str, extension: str) -> str:
    """
    Convert book title to a filesystem-safe filename.
    Removes characters not allowed in filenames on any major OS.
    """
    # Strip characters invalid in Windows/Linux filenames
    safe = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", title)
    safe = safe.strip(". ")  # strip leading/trailing dots and spaces
    safe = safe[:100]  # cap length

    if not safe:
        safe = "Book"

    return f"{safe}.{extension}"


def resolve_output_path(title: str, fmt: str) -> Path:
    """
    Build the full output file path for the given book title and format.

    Args:
        title: Book title string
        fmt: "pdf" or "docx"

    Returns:
        Full absolute Path for the output file on the Desktop
    """
    desktop = get_desktop_path()
    filename = _safe_filename(title, fmt.lower())
    return desktop / filename


# ─────────────────────────────────────────────
# Output dispatcher
# ─────────────────────────────────────────────

def save_book(book, fmt: str, output_path: Path) -> Path:
    """
    Route book to the correct format generator and save it.

    Args:
        book: Book dataclass instance
        fmt: "pdf" or "docx"
        output_path: Full path where output should be written

    Returns:
        Path to the saved file
    """
    fmt = fmt.lower().strip()

    if fmt == "pdf":
        from output_pdf import generate_pdf
        return generate_pdf(book, output_path)

    elif fmt == "docx":
        from output_docx import generate_docx
        return generate_docx(book, output_path)

    else:
        raise ValueError(f"Unsupported output format: '{fmt}'. Choose 'pdf' or 'docx'.")


def get_file_size_str(path: Path) -> str:
    """Return a human-readable file size string."""
    try:
        size_bytes = path.stat().st_size
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.2f} MB"
    except Exception:
        return "unknown size"