"""
cli.py
Interactive CLI interface for cypher-aibookgenerator.
Built with Rich for a clean, modern terminal experience.
"""

import logging
import sys
import time
from typing import Optional

from rich import box
from rich.align import Align
from rich.columns import Columns
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.prompt import Confirm, Prompt
from rich.rule import Rule
from rich.style import Style
from rich.table import Table
from rich.text import Text

from prompt_processing import (
    sanitize_prompt,
    validate_author,
    validate_chapter_count,
    validate_chapter_names,
    validate_output_format,
    validate_title,
)
from output import resolve_output_path, get_desktop_path

logger = logging.getLogger(__name__)
console = Console()

# ─────────────────────────────────────────────
# Theme / palette
# ─────────────────────────────────────────────
ACCENT = "cyan"
MUTED = "dim white"
SUCCESS = "green"
WARNING = "yellow"
ERROR = "red"
HEADER_BG = "on grey11"

# ─────────────────────────────────────────────
# Genre list
# ─────────────────────────────────────────────
GENRES = [
    "Horror",
    "Sci Fi",
    "Philosophical",
    "Documentary",
    "Dark Romance",
    "Romance",
    "Fantasy",
    "Comedy",
    "Sad",
    "Love Stories",
    "Love and Drama",
    "Adventure and Power",
    "Historical",
    "Fiction",
    "Murder Mystery",
    "Mystery",
    "Thriller",
    "Historical Fiction",
    "Young Adult",
    "Literary Fiction",
    "Memoir / Auto Biography",
    "Biography",
    "Self Help",
    "True Crime",
    "Dystopian",
    "Paranormal Activity",
    "Paranormal Romance",
    "Investigative Journalism",
]

BANNER = r"""
  ██████╗██╗   ██╗██████╗ ██╗  ██╗███████╗██████╗
 ██╔════╝╚██╗ ██╔╝██╔══██╗██║  ██║██╔════╝██╔══██╗
 ██║      ╚████╔╝ ██████╔╝███████║█████╗  ██████╔╝
 ██║       ╚██╔╝  ██╔═══╝ ██╔══██║██╔══╝  ██╔══██╗
 ╚██████╗   ██║   ██║     ██║  ██║███████╗██████╔╝
  ╚═════╝   ╚═╝   ╚═╝     ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝

         AI Book Generator
"""


# ─────────────────────────────────────────────
# Display helpers
# ─────────────────────────────────────────────

def print_banner() -> None:
    """Display the application banner."""
    console.print()
    console.print(
        Panel(
            Align.center(
                Text(BANNER, style=f"bold {ACCENT}"),
            ),
            border_style=ACCENT,
            padding=(0, 2),
        )
    )
    console.print(
        Align.center(
            Text(
                "Powered by Ollama · llama3.2:3b · Local AI · No Internet Required",
                style=MUTED,
            )
        )
    )
    console.print()


def print_section(title: str) -> None:
    """Print a styled section separator."""
    console.print(Rule(f"[bold {ACCENT}]{title}[/]", style=ACCENT))


def print_success(msg: str) -> None:
    console.print(f"[{SUCCESS}]✔ {msg}[/]")


def print_warning(msg: str) -> None:
    console.print(f"[{WARNING}]⚠ {msg}[/]")


def print_error(msg: str) -> None:
    console.print(f"[{ERROR}]✘ {msg}[/]")


def print_info(msg: str) -> None:
    console.print(f"[{ACCENT}]ℹ {msg}[/]")


def show_system_info(gpu_info: dict) -> None:
    """Display system hardware info."""
    table = Table(box=box.ROUNDED, border_style="dim cyan", show_header=False, padding=(0, 1))
    table.add_column("Key", style=f"bold {ACCENT}", no_wrap=True)
    table.add_column("Value", style="white")

    table.add_row("🖥  Model", "llama3.2:3b (Ollama)")
    table.add_row(
        "⚡ Backend",
        f"[green]{gpu_info['backend']}[/]" if gpu_info["has_gpu"] else f"[yellow]{gpu_info['backend']}[/]",
    )
    if gpu_info["has_gpu"]:
        table.add_row("🎮 GPU", gpu_info["gpu_name"])
    table.add_row("📁 Output", str(get_desktop_path()))

    console.print(
        Panel(table, title="[bold]System Info[/]", border_style="dim cyan", padding=(0, 1))
    )
    console.print()


# ─────────────────────────────────────────────
# Input collection
# ─────────────────────────────────────────────

def collect_book_title() -> str:
    """Prompt user for book title with validation."""
    while True:
        raw = Prompt.ask(f"[bold {ACCENT}]📖 Book Title[/]")
        try:
            title = validate_title(raw)
            print_success(f"Title set: {title}")
            return title
        except ValueError as exc:
            print_error(str(exc))


def collect_author() -> str:
    """Prompt user for author name."""
    raw = Prompt.ask(
        f"[bold {ACCENT}]✍  Author Name[/]",
        default="Anonymous",
    )
    author = validate_author(raw)
    print_success(f"Author: {author}")
    return author


def collect_genre() -> str:
    """Prompt user to select a genre interactively."""
    console.print(f"[{MUTED}]Select a genre for your book.[/]")
    
    # Display genres in a numbered format
    for idx, genre in enumerate(GENRES, 1):
        console.print(f"  {idx:2d}. {genre}")
    
    console.print()
    
    while True:
        raw = Prompt.ask(
            f"[bold {ACCENT}]🎭 Genre[/]",
            default="1",
        )
        try:
            choice = int(raw.strip())
            if 1 <= choice <= len(GENRES):
                genre = GENRES[choice - 1]
                print_success(f"Genre selected: {genre}")
                return genre
            else:
                print_error(f"Please enter a number between 1 and {len(GENRES)}.")
        except ValueError:
            print_error("Please enter a valid number.")


def collect_chapter_count() -> int:
    """Prompt user for number of chapters."""
    while True:
        raw = Prompt.ask(
            f"[bold {ACCENT}]📑 Number of Chapters[/]",
            default="5",
        )
        try:
            count = validate_chapter_count(raw, default=5)
            print_success(f"Chapters: {count}")
            return count
        except ValueError as exc:
            print_error(str(exc))


def collect_chapter_names(expected_count: int) -> list[str]:
    """
    Prompt user for chapter names (comma-separated).
    Returns empty list if user skips → triggers auto-generation.
    """
    console.print(
        f"[{MUTED}]Enter chapter names separated by commas, or press Enter to auto-generate.[/]"
    )
    raw = Prompt.ask(
        f"[bold {ACCENT}]📝 Chapter Names[/]",
        default="",
    )

    if not raw.strip():
        print_info("Chapter names will be auto-generated by AI.")
        return []

    names = validate_chapter_names(raw, expected_count)

    if len(names) < expected_count:
        print_warning(
            f"Only {len(names)} name(s) provided for {expected_count} chapters. "
            f"Remaining will be auto-generated."
        )
    else:
        print_success(f"Loaded {len(names)} chapter name(s).")

    return names


def collect_prompt() -> str:
    """Collect and validate the user's book prompt (up to 5000 chars)."""
    console.print(
        f"[{MUTED}]Describe your book topic, style, themes, and audience. "
        f"(Max 5000 characters. Press Enter twice when done.)[/]"
    )
    console.print()

    lines = []
    print(f"\033[96mPrompt (end with a blank line):\033[0m")

    try:
        while True:
            line = input()
            if line == "" and lines and lines[-1] == "":
                break
            lines.append(line)
    except EOFError:
        pass

    raw = "\n".join(lines).strip()

    if not raw:
        # Default prompt
        raw = "Write a general informative book with interesting and engaging content."
        print_warning("No prompt provided. Using default.")

    try:
        clean_prompt = sanitize_prompt(raw)
        print_success(f"Prompt accepted ({len(clean_prompt)} characters).")
        return clean_prompt
    except ValueError as exc:
        print_error(f"Prompt issue: {exc}")
        return "Write a general informative book with interesting content."


def collect_output_format() -> str:
    """Prompt user to choose PDF or DOCX output."""
    while True:
        raw = Prompt.ask(
            f"[bold {ACCENT}]💾 Output Format[/]",
            choices=["pdf", "docx"],
            default="pdf",
        )
        try:
            fmt = validate_output_format(raw)
            print_success(f"Output format: {fmt.upper()}")
            return fmt
        except ValueError as exc:
            print_error(str(exc))


def confirm_settings(
    title: str,
    author: str,
    genre: str,
    num_chapters: int,
    chapter_names: list[str],
    user_prompt: str,
    output_format: str,
    output_path,
) -> bool:
    """Show a summary table and ask for confirmation."""
    console.print()
    print_section("Confirm Book Settings")
    console.print()

    table = Table(box=box.ROUNDED, border_style=ACCENT, show_header=False, padding=(0, 1))
    table.add_column("Field", style=f"bold {ACCENT}", no_wrap=True)
    table.add_column("Value", style="white")

    table.add_row("📖 Title", title)
    table.add_row("✍  Author", author)
    table.add_row("🎭 Genre", genre)
    table.add_row("📑 Chapters", str(num_chapters))

    if chapter_names:
        names_str = ", ".join(chapter_names[:3])
        if len(chapter_names) > 3:
            names_str += f" ... (+{len(chapter_names) - 3} more)"
        table.add_row("📝 Chapter Names", names_str)
    else:
        table.add_row("📝 Chapter Names", "[dim]Auto-generate[/]")

    prompt_preview = user_prompt[:80] + ("..." if len(user_prompt) > 80 else "")
    table.add_row("💬 Prompt", prompt_preview)
    table.add_row("💾 Format", output_format.upper())
    table.add_row("📂 Output Path", str(output_path))

    console.print(table)
    console.print()

    return Confirm.ask(f"[bold {ACCENT}]Proceed with book generation?[/]", default=True)


# ─────────────────────────────────────────────
# Progress display
# ─────────────────────────────────────────────

class GenerationDisplay:
    """Manages the live progress display during book generation."""

    def __init__(self, num_chapters: int):
        self.num_chapters = num_chapters
        self.progress = Progress(
            SpinnerColumn(spinner_name="dots", style=f"bold {ACCENT}"),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=30, style=ACCENT, complete_style=SUCCESS),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console,
            transient=False,
        )
        self.task_id = self.progress.add_task(
            f"[bold]Generating book...[/]", total=num_chapters
        )
        self._chapter_tokens: list[str] = []
        self._live_console = Console(stderr=False)

    def start(self):
        self.progress.start()

    def stop(self):
        self.progress.stop()

    def on_chapter_start(self, chapter_num: int, chapter_title: str, total: int):
        self.progress.update(
            self.task_id,
            description=f"[bold {ACCENT}]Chapter {chapter_num}/{total}[/] · [italic]{chapter_title}[/]",
        )
        self._chapter_tokens = []
        console.print(f"\n[bold {ACCENT}]▶ Chapter {chapter_num}: {chapter_title}[/]")

    def on_token(self, token: str):
        self._chapter_tokens.append(token)
        # Print every 50 tokens to avoid flooding terminal
        if len(self._chapter_tokens) % 50 == 0:
            snippet = "".join(self._chapter_tokens[-50:]).replace("\n", " ")[:60]
            console.print(f"[dim]{snippet}[/]", end="", highlight=False)

    def on_chapter_complete(self, chapter_num: int, word_count: int, total: int):
        console.print()  # newline after streamed tokens
        self.progress.advance(self.task_id)
        console.print(
            f"[{SUCCESS}]  ✔ Chapter {chapter_num} complete — {word_count:,} words[/]"
        )


# ─────────────────────────────────────────────
# Final summary display
# ─────────────────────────────────────────────

def show_completion_summary(book, output_path, file_size: str) -> None:
    """Display a final success summary after book generation."""
    console.print()
    print_section("Book Generation Complete")
    console.print()

    table = Table(box=box.ROUNDED, border_style=SUCCESS, show_header=False, padding=(0, 1))
    table.add_column("Field", style=f"bold {SUCCESS}", no_wrap=True)
    table.add_column("Value", style="white")

    table.add_row("📖 Title", book.title)
    table.add_row("✍  Author", book.author)
    table.add_row("📑 Chapters", str(len(book.chapters)))
    table.add_row("📊 Total Words", f"{book.total_word_count:,}")
    table.add_row("📂 Saved To", str(output_path))
    table.add_row("📦 File Size", file_size)

    console.print(table)
    console.print()
    console.print(
        Panel(
            Align.center(
                Text("Your book has been saved to your Desktop!", style=f"bold {SUCCESS}")
            ),
            border_style=SUCCESS,
        )
    )
    console.print()


# ─────────────────────────────────────────────
# Startup checks display
# ─────────────────────────────────────────────

def show_startup_check(label: str, status: str, success: bool) -> None:
    icon = "✔" if success else "✘"
    color = SUCCESS if success else ERROR
    console.print(f"  [{color}]{icon}[/] {label}: [{color}]{status}[/]")


# ─────────────────────────────────────────────
# Main CLI entry point
# ─────────────────────────────────────────────

def run_cli(gpu_info: dict) -> dict:
    """
    Run the full interactive CLI and return collected book parameters.

    Returns a dict with keys:
        title, author, genre, num_chapters, chapter_names, user_prompt, output_format, output_path
    """
    print_banner()
    show_system_info(gpu_info)

    # ── Collect inputs ──────────────────────────
    print_section("Book Configuration")
    console.print()

    title = collect_book_title()
    author = collect_author()
    console.print()
    
    genre = collect_genre()
    console.print()

    num_chapters = collect_chapter_count()
    chapter_names = collect_chapter_names(num_chapters)
    console.print()

    print_section("Book Topic and Style")
    console.print()
    user_prompt = collect_prompt()
    console.print()

    print_section("Output Settings")
    console.print()
    output_format = collect_output_format()

    output_path = resolve_output_path(title, output_format)
    console.print()

    # ── Confirm ─────────────────────────────────
    confirmed = confirm_settings(
        title, author, genre, num_chapters, chapter_names,
        user_prompt, output_format, output_path
    )

    if not confirmed:
        console.print(f"\n[{WARNING}]Generation cancelled by user.[/]\n")
        sys.exit(0)

    return {
        "title": title,
        "author": author,
        "genre": genre,
        "num_chapters": num_chapters,
        "chapter_names": chapter_names,
        "user_prompt": user_prompt,
        "output_format": output_format,
        "output_path": output_path,
    }