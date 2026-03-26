"""
run.py
Entry point for cypher-aibookgenerator.

Execution flow:
  1. Ensure Ollama is running
  2. Ensure llama3.2:3b model is available
  3. Launch CLI to collect user input
  4. Auto-generate chapter names if needed
  5. Generate book chapter by chapter
  6. Save output to Desktop
"""

import logging
import sys
import time

# ─────────────────────────────────────────────
# Logging setup (file + stderr)
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("cypher_aibookgenerator.log", encoding="utf-8"),
        logging.StreamHandler(sys.stderr),
    ],
)
# Silence noisy third-party loggers
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def main():
    # Late imports so logging is configured first
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn

    from processors import (
        ensure_ollama_running,
        ensure_model_available,
        detect_gpu,
    )
    from cli import (
        console,
        print_banner,
        print_section,
        print_success,
        print_error,
        print_info,
        print_warning,
        show_startup_check,
        run_cli,
        GenerationDisplay,
        show_completion_summary,
    )
    from generation import generate_book, generate_chapter_names
    from output import save_book, get_file_size_str

    # ── 1. System checks ──────────────────────────
    console.print()
    print_section("System Startup")
    console.print()

    # GPU detection
    gpu_info = detect_gpu()
    show_startup_check(
        "Hardware Backend",
        gpu_info["backend"],
        gpu_info["has_gpu"],
    )

    # Ollama check
    console.print("  Checking Ollama server...", end=" ")
    if not ensure_ollama_running():
        print_error(
            "Ollama could not be started. Please install Ollama and try again.\n"
            "  Install: https://ollama.com/download"
        )
        sys.exit(1)
    show_startup_check("Ollama Server", "Running", True)

    # Model check
    with Progress(
        SpinnerColumn(),
        TextColumn("  Checking model llama3.2:3b..."),
        transient=True,
        console=console,
    ) as progress:
        task = progress.add_task("checking", total=None)

        def _model_progress(status: str):
            progress.update(task, description=f"  [dim]{status}[/]")

        model_ok = ensure_model_available(progress_callback=_model_progress)

    if not model_ok:
        print_error("Could not ensure llama3.2:3b is available. Check your Ollama installation.")
        sys.exit(1)
    show_startup_check("Model llama3.2:3b", "Ready", True)

    console.print()

    # ── 2. CLI input collection ───────────────────
    params = run_cli(gpu_info)

    title = params["title"]
    author = params["author"]
    genre = params["genre"]
    num_chapters = params["num_chapters"]
    chapter_names = params["chapter_names"]
    user_prompt = params["user_prompt"]
    output_format = params["output_format"]
    output_path = params["output_path"]

    # ── 3. Auto-generate chapter names if needed ──
    if len(chapter_names) < num_chapters:
        missing = num_chapters - len(chapter_names)
        print_info(f"Auto-generating {missing} chapter name(s) with AI...")

        with Progress(
            SpinnerColumn(),
            TextColumn("  Generating chapter names..."),
            transient=True,
            console=console,
        ) as progress:
            progress.add_task("gen_names", total=None)
            auto_names = generate_chapter_names(
                title=title,
                count=missing,
                genre=genre,
                user_prompt=user_prompt,
            )

        # Append auto names to user-provided ones
        chapter_names = chapter_names + auto_names
        print_success(f"Chapter names ready: {len(chapter_names)} total")
        for i, name in enumerate(chapter_names, 1):
            console.print(f"  [dim]{i}.[/] {name}")
        console.print()

    # ── 4. Generate book ──────────────────────────
    print_section("Generating Your Book")
    console.print()

    display = GenerationDisplay(num_chapters)
    display.start()

    start_time = time.time()

    try:
        book = generate_book(
            title=title,
            author=author,
            genre=genre,
            chapter_names=chapter_names,
            num_chapters=num_chapters,
            user_prompt=user_prompt,
            on_chapter_start=display.on_chapter_start,
            on_chapter_complete=display.on_chapter_complete,
            on_token=display.on_token,
        )
    except Exception as exc:
        display.stop()
        print_error(f"Book generation failed: {exc}")
        logger.exception("Book generation failed")
        sys.exit(1)
    finally:
        display.stop()

    elapsed = time.time() - start_time
    print_success(
        f"Generation complete in {elapsed / 60:.1f} minutes. "
        f"{book.total_word_count:,} words across {len(book.chapters)} chapters."
    )
    console.print()

    # ── 5. Save output ────────────────────────────
    print_section("Saving Output")
    console.print()

    with Progress(
        SpinnerColumn(),
        TextColumn(f"  Saving {output_format.upper()} to Desktop..."),
        transient=True,
        console=console,
    ) as progress:
        progress.add_task("saving", total=None)
        try:
            saved_path = save_book(book, output_format, output_path)
        except Exception as exc:
            print_error(f"Failed to save {output_format.upper()}: {exc}")
            logger.exception("Failed to save book")
            sys.exit(1)

    file_size = get_file_size_str(saved_path)
    show_completion_summary(book, saved_path, file_size)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[Interrupted by user. Goodbye!]\n")
        sys.exit(0)