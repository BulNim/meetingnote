from collections.abc import Iterable


def parse_todos(todo_text: str | None) -> Iterable[tuple[str, str, str]]:
    if not todo_text:
        return []

    parsed: list[tuple[str, str, str]] = []
    for line in todo_text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = [part.strip() for part in line.split("|", 2)]
        what = parts[0] or "미정"
        who = parts[1] if len(parts) > 1 and parts[1] else "미정"
        when = parts[2] if len(parts) > 2 and parts[2] else "미정"
        parsed.append((what, who, when))
    return parsed
