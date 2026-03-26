"""
prompt_processing.py
Sanitize and validate all user input before LLM processing.
"""

import re
import logging

logger = logging.getLogger(__name__)

# Allowed characters in final output
ALLOWED_OUTPUT_PATTERN = re.compile(r"[^A-Za-z0-9 .,?'\n\r\t-]")

# Max prompt length
MAX_PROMPT_LENGTH = 5000


def sanitize_prompt(text: str) -> str:
    """
    Keep all ASCII printable chars in the user prompt (for LLM input).
    Strips leading/trailing whitespace and collapses excessive blank lines.
    """
    if not isinstance(text, str):
        raise ValueError("Prompt must be a string.")

    # Only keep printable ASCII (32-126) plus newlines/tabs
    cleaned = "".join(
        ch for ch in text if (32 <= ord(ch) <= 126) or ch in ("\n", "\r", "\t")
    )

    # Collapse 3+ consecutive newlines into 2
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = cleaned.strip()

    if len(cleaned) == 0:
        raise ValueError("Prompt is empty after sanitization.")

    if len(cleaned) > MAX_PROMPT_LENGTH:
        logger.warning(
            "Prompt truncated from %d to %d characters.", len(cleaned), MAX_PROMPT_LENGTH
        )
        cleaned = cleaned[:MAX_PROMPT_LENGTH]

    return cleaned


def sanitize_output_text(text: str) -> str:
    """
    Sanitize final book output: only A-Z, a-z, 0-9, space,
    basic punctuation (. , ? ' - ), and whitespace characters.
    All other characters are removed.
    """
    if not isinstance(text, str):
        return ""

    # Remove disallowed characters
    cleaned = ALLOWED_OUTPUT_PATTERN.sub("", text)

    # Normalize multiple spaces to single space (preserve newlines)
    lines = cleaned.split("\n")
    lines = [re.sub(r" {2,}", " ", line) for line in lines]
    cleaned = "\n".join(lines)

    # Collapse excessive blank lines
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    return cleaned.strip()


def validate_title(title: str) -> str:
    """Validate and clean book title."""
    if not title or not title.strip():
        raise ValueError("Book title cannot be empty.")

    title = title.strip()

    if len(title) > 200:
        raise ValueError("Book title must be under 200 characters.")

    # Allow alphanumeric, spaces, basic punctuation for title
    safe = re.sub(r"[^A-Za-z0-9 .,?'\-!:]", "", title)
    if not safe.strip():
        raise ValueError("Book title contains no valid characters.")

    return safe.strip()


def validate_author(author: str) -> str:
    """Validate and clean author name."""
    if not author or not author.strip():
        return "Unknown Author"

    author = author.strip()
    safe = re.sub(r"[^A-Za-z0-9 .,'\-]", "", author)
    return safe.strip() if safe.strip() else "Unknown Author"


def validate_chapter_count(value: str, default: int = 5) -> int:
    """Parse and validate chapter count."""
    if not value or not value.strip():
        return default

    try:
        count = int(value.strip())
    except ValueError:
        raise ValueError("Number of chapters must be a whole number.")

    if count < 1:
        raise ValueError("Number of chapters must be at least 1.")
    if count > 30:
        raise ValueError("Number of chapters cannot exceed 30.")

    return count


def validate_chapter_names(raw: str, expected_count: int) -> list[str]:
    """
    Parse comma-separated chapter names.
    Returns a list (may be shorter than expected_count; auto-fill handled elsewhere).
    """
    if not raw or not raw.strip():
        return []

    parts = [p.strip() for p in raw.split(",") if p.strip()]
    cleaned = []
    for name in parts:
        safe = re.sub(r"[^A-Za-z0-9 .,?'\-!:]", "", name).strip()
        if safe:
            cleaned.append(safe)

    return cleaned


def validate_output_format(fmt: str) -> str:
    """Validate output format choice."""
    fmt = fmt.strip().lower()
    if fmt not in ("pdf", "docx"):
        raise ValueError("Output format must be 'pdf' or 'docx'.")
    return fmt


def build_book_prompt(
    title: str,
    author: str,
    genre: str,
    chapter_names: list[str],
    chapter_number: int,
    total_chapters: int,
    user_prompt: str,
    previous_summary: str = "",
) -> str:
    """
    Build a structured LLM prompt for generating a single chapter.
    """
    chapter_title = chapter_names[chapter_number - 1] if chapter_number <= len(chapter_names) else f"Chapter {chapter_number}"

    context_block = ""
    if previous_summary:
        context_block = f"\nPrevious chapters summary (DO NOT repeat this content):\n{previous_summary}\n"

    prompt = (
        f"You are a professional book author writing the book titled '{title}' by {author}.\n"
        f"Genre: {genre}.\n"
        f"This book has {total_chapters} chapters total.\n"
        f"{context_block}\n"
        f"Now write Chapter {chapter_number}: '{chapter_title}'.\n"
        f"Book topic and style guidance: {user_prompt}\n\n"
        f"Rules:\n"
        f"- Write ONLY the chapter content (no meta-commentary, no notes to reader).\n"
        f"- Do NOT repeat ideas from previous chapters.\n"
        f"- Maintain logical narrative flow.\n"
        f"- Professional, clean writing style.\n"
        f"- At least 4 substantial paragraphs.\n"
        f"- Do NOT use bullet points, markdown, or special symbols.\n"
        f"- Only use plain English sentences and paragraphs.\n"
        f"- Start directly with the chapter content.\n"
    )
    return prompt


def build_chapter_names_prompt(title: str, count: int, genre: str, user_prompt: str) -> str:
    """Build a prompt to auto-generate chapter names."""
    return (
        f"Generate exactly {count} chapter titles for a book titled '{title}'.\n"
        f"Genre: {genre}.\n"
        f"Book topic: {user_prompt}\n"
        f"Rules:\n"
        f"- Return ONLY the chapter titles, one per line.\n"
        f"- No numbering, no extra text, no explanations.\n"
        f"- Each title should be descriptive and unique.\n"
        f"- Plain English only, no special characters.\n"
        f"Example output format:\n"
        f"The Beginning of Everything\n"
        f"Foundations of Understanding\n"
        f"The Path Forward\n"
    )


def build_summary_prompt(chapter_content: str, chapter_title: str) -> str:
    """Build a prompt to summarize a chapter for context continuity."""
    return (
        f"Summarize the following chapter titled '{chapter_title}' in 2-3 sentences.\n"
        f"Focus on key ideas and events. Plain English only.\n\n"
        f"Chapter content:\n{chapter_content[:3000]}\n\n"
        f"Summary:"
    )