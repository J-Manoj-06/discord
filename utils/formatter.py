from typing import Iterable


def progress_bar(current: int, total: int, size: int = 16) -> str:
    if total <= 0:
        total = 1
    ratio = max(0.0, min(1.0, current / total))
    filled = int(round(size * ratio))
    return "█" * filled + "░" * (size - filled)


def format_duration(seconds: int) -> str:
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    sec = seconds % 60
    parts = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if sec or not parts:
        parts.append(f"{sec}s")
    return " ".join(parts)


def chunked_lines(items: Iterable[str], chunk_size: int = 10) -> list[str]:
    buffer = []
    current = []
    for item in items:
        current.append(item)
        if len(current) == chunk_size:
            buffer.append("\n".join(current))
            current = []
    if current:
        buffer.append("\n".join(current))
    return buffer
