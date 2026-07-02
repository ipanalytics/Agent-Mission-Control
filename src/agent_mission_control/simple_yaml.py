"""Small YAML subset reader/writer used by Agent Mission Control templates.

Supported input is intentionally narrow: top-level mappings, scalar values, and
top-level lists written with ``- item``. That keeps the 1.0 release dependency
free while covering the project contract and policy files.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


class SimpleYAMLError(ValueError):
    """Raised when a file does not fit the supported YAML subset."""


def _strip_comment(line: str) -> str:
    in_quote: str | None = None
    escaped = False
    for index, char in enumerate(line):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char in {"'", '"'}:
            if in_quote == char:
                in_quote = None
            elif in_quote is None:
                in_quote = char
        if char == "#" and in_quote is None:
            return line[:index]
    return line


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "":
        return ""
    if value in {"true", "True"}:
        return True
    if value in {"false", "False"}:
        return False
    if value in {"null", "None", "~"}:
        return None
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    try:
        return int(value)
    except ValueError:
        return value


def loads(text: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current_key: str | None = None
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = _strip_comment(raw_line).rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        if indent == 0 and ":" in stripped and not stripped.startswith("-"):
            key, value = stripped.split(":", 1)
            key = key.strip()
            if not key:
                raise SimpleYAMLError(f"line {line_number}: empty key")
            value = value.strip()
            if value == "":
                data[key] = []
                current_key = key
            else:
                data[key] = _parse_scalar(value)
                current_key = None
            continue
        if indent > 0 and stripped.startswith("- "):
            if current_key is None:
                raise SimpleYAMLError(f"line {line_number}: list item without key")
            if not isinstance(data[current_key], list):
                raise SimpleYAMLError(f"line {line_number}: key is not a list")
            data[current_key].append(_parse_scalar(stripped[2:]))
            continue
        raise SimpleYAMLError(f"line {line_number}: unsupported YAML syntax")
    return data


def load_file(path: str | Path) -> dict[str, Any]:
    return loads(Path(path).read_text(encoding="utf-8"))


def dumps(data: dict[str, Any]) -> str:
    lines: list[str] = []
    for key, value in data.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {item}")
        elif isinstance(value, bool):
            lines.append(f"{key}: {'true' if value else 'false'}")
        elif value is None:
            lines.append(f"{key}: null")
        else:
            lines.append(f"{key}: {value}")
    return "\n".join(lines) + "\n"

