"""
generation.py
High-level LLM generation logic — orchestrates multi-chapter book creation.
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

from processors import generate_text
from prompt_processing import (
    build_book_prompt,
    build_chapter_names_prompt,
    build_summary_prompt,
    sanitize_output_text,
)

logger = logging.getLogger(__name__)


@dataclass
class Chapter:
    number: int
    title: str
    content: str
    word_count: int = 0

    def __post_init__(self):
        self.word_count = len(self.content.split())


@dataclass
class Book:
    title: str
    author: str
    chapters: list[Chapter] = field(default_factory=list)
    total_word_count: int = 0

    def add_chapter(self, chapter: Chapter):
        self.chapters.append(chapter)
        self.total_word_count += chapter.word_count


# ─────────────────────────────────────────────
# Chapter name generation
# ─────────────────────────────────────────────

def generate_chapter_names(
    title: str,
    count: int,
    genre: str,
    user_prompt: str,
    status_callback: Optional[Callable[[str], None]] = None,
) -> list[str]:
    """Auto-generate chapter names using the LLM."""
    if status_callback:
        status_callback(f"Generating {count} chapter names...")

    prompt = build_chapter_names_prompt(title, count, genre, user_prompt)

    try:
        raw = generate_text(prompt, temperature=0.8)
    except Exception as exc:
        logger.error("Failed to generate chapter names: %s", exc)
        # Fallback to generic names
        return [f"Chapter {i}" for i in range(1, count + 1)]

    # Parse one name per line
    lines = [ln.strip() for ln in raw.strip().split("\n") if ln.strip()]

    # Strip any leading numbering like "1." or "1)"
    cleaned = []
    for ln in lines:
        # Remove patterns like "1. ", "1) ", "Chapter 1: "
        ln = __import__("re").sub(r"^(\d+[\.\)]\s*|Chapter\s+\d+:\s*)", "", ln, flags=__import__("re").IGNORECASE).strip()
        if ln:
            cleaned.append(sanitize_output_text(ln))

    # Pad or trim to exact count
    while len(cleaned) < count:
        cleaned.append(f"Chapter {len(cleaned) + 1}")
    cleaned = cleaned[:count]

    logger.info("Generated chapter names: %s", cleaned)
    return cleaned


# ─────────────────────────────────────────────
# Single chapter generation
# ─────────────────────────────────────────────

def generate_chapter(
    title: str,
    author: str,
    genre: str,
    chapter_names: list[str],
    chapter_number: int,
    total_chapters: int,
    user_prompt: str,
    previous_summary: str = "",
    stream_callback: Optional[Callable[[str], None]] = None,
    retries: int = 2,
) -> Chapter:
    """Generate content for a single chapter with retry logic."""
    chapter_title = (
        chapter_names[chapter_number - 1]
        if chapter_number <= len(chapter_names)
        else f"Chapter {chapter_number}"
    )

    prompt = build_book_prompt(
        title=title,
        author=author,
        genre=genre,
        chapter_names=chapter_names,
        chapter_number=chapter_number,
        total_chapters=total_chapters,
        user_prompt=user_prompt,
        previous_summary=previous_summary,
    )

    last_exc = None
    for attempt in range(1, retries + 2):
        try:
            logger.info(
                "Generating chapter %d/%d (attempt %d): %s",
                chapter_number,
                total_chapters,
                attempt,
                chapter_title,
            )

            raw_content = generate_text(
                prompt,
                temperature=0.75,
                stream_callback=stream_callback,
            )

            # Sanitize output
            content = sanitize_output_text(raw_content)

            if len(content.split()) < 100:
                logger.warning(
                    "Chapter %d too short (%d words). Retrying...",
                    chapter_number,
                    len(content.split()),
                )
                last_exc = ValueError("Generated content too short.")
                time.sleep(1)
                continue

            return Chapter(
                number=chapter_number,
                title=chapter_title,
                content=content,
            )

        except Exception as exc:
            logger.error(
                "Chapter %d generation attempt %d failed: %s",
                chapter_number,
                attempt,
                exc,
            )
            last_exc = exc
            time.sleep(2)

    # If all retries fail, return placeholder
    logger.error(
        "All attempts to generate chapter %d failed. Using placeholder.",
        chapter_number,
    )
    placeholder = (
        f"This chapter could not be generated due to a technical error. "
        f"Please re-run the application to regenerate {chapter_title}."
    )
    return Chapter(
        number=chapter_number,
        title=chapter_title,
        content=placeholder,
    )


# ─────────────────────────────────────────────
# Chapter summary for context continuity
# ─────────────────────────────────────────────

def summarize_chapter(chapter: Chapter) -> str:
    """Generate a brief summary of a chapter for use as context in subsequent chapters."""
    prompt = build_summary_prompt(chapter.content, chapter.title)
    try:
        raw = generate_text(prompt, temperature=0.3)
        return sanitize_output_text(raw).strip()
    except Exception as exc:
        logger.warning("Failed to summarize chapter %d: %s", chapter.number, exc)
        # Return first 200 chars of content as fallback summary
        return chapter.content[:200] + "..."


# ─────────────────────────────────────────────
# Full book generation orchestrator
# ─────────────────────────────────────────────

def generate_book(
    title: str,
    author: str,
    genre: str,
    chapter_names: list[str],
    num_chapters: int,
    user_prompt: str,
    on_chapter_start: Optional[Callable[[int, str, int], None]] = None,
    on_chapter_complete: Optional[Callable[[int, int, int], None]] = None,
    on_token: Optional[Callable[[str], None]] = None,
) -> Book:
    """
    Generate a complete book with the specified number of chapters.

    Args:
        title: Book title
        author: Author name
        genre: Book genre
        chapter_names: Pre-defined chapter names (may be empty → auto-generated)
        num_chapters: Total number of chapters
        user_prompt: User's topic/style guidance
        on_chapter_start: callback(chapter_num, chapter_title, total)
        on_chapter_complete: callback(chapter_num, word_count, total)
        on_token: callback(token_str) for live streaming display
    """
    book = Book(title=title, author=author)
    previous_summary = ""

    for chapter_num in range(1, num_chapters + 1):
        chapter_title = (
            chapter_names[chapter_num - 1]
            if chapter_num <= len(chapter_names)
            else f"Chapter {chapter_num}"
        )

        if on_chapter_start:
            on_chapter_start(chapter_num, chapter_title, num_chapters)

        chapter = generate_chapter(
            title=title,
            author=author,
            genre=genre,
            chapter_names=chapter_names,
            chapter_number=chapter_num,
            total_chapters=num_chapters,
            user_prompt=user_prompt,
            previous_summary=previous_summary,
            stream_callback=on_token,
        )

        book.add_chapter(chapter)

        if on_chapter_complete:
            on_chapter_complete(chapter_num, chapter.word_count, num_chapters)

        # Build running summary for context continuity (skip for last chapter)
        if chapter_num < num_chapters:
            summary = summarize_chapter(chapter)
            if previous_summary:
                # Append to rolling summary, keep last ~500 chars
                combined = f"{previous_summary} {summary}"
                previous_summary = combined[-500:] if len(combined) > 500 else combined
            else:
                previous_summary = summary

    logger.info(
        "Book generation complete: %d chapters, %d total words.",
        len(book.chapters),
        book.total_word_count,
    )
    return book