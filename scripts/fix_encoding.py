from __future__ import annotations

import argparse
from pathlib import Path


TEXT_EXTENSIONS = {
    ".py",
    ".sql",
    ".txt",
    ".md",
    ".json",
    ".jsonl",
    ".ini",
    ".cfg",
    ".yml",
    ".yaml",
}

SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".idea",
    ".vscode",
}

MOJIBAKE_CHARS = "ÐÑРСЃЌÂÃ¤"


# Проверяет, содержит ли текст явные признаки битой кодировки.
def has_suspect_text(text: str) -> bool:
    if any(ch in text for ch in MOJIBAKE_CHARS):
        return True
    return "???" in text


# Оценивает качество текста, чтобы выбрать самый читаемый вариант исправления.
def text_score(text: str) -> int:
    cyrillic = sum(
        1
        for ch in text
        if "А" <= ch <= "я" or ch in "Ёё"
    )
    latin = sum(1 for ch in text if "A" <= ch <= "z")
    bad = sum(text.count(ch) for ch in MOJIBAKE_CHARS)
    questions = text.count("???")
    controls = sum(
        1
        for ch in text
        if ord(ch) < 32 and ch not in "\r\n\t"
    )
    return cyrillic * 4 + latin - bad * 6 - questions * 8 - controls * 20


# Пытается восстановить текст через перекодировку из исходной кодировки.
def decode_roundtrip(text: str, source_encoding: str) -> str | None:
    try:
        return text.encode(source_encoding).decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return None


# Строит возможные исправленные варианты подозрительного фрагмента текста.
def candidate_variants(text: str) -> list[str]:
    variants = {text}
    for encoding in ("cp1251", "latin1", "cp866"):
        fixed = decode_roundtrip(text, encoding)
        if fixed:
            variants.add(fixed)
            fixed_twice = decode_roundtrip(fixed, encoding)
            if fixed_twice:
                variants.add(fixed_twice)
    return list(variants)


# Исправляет одну строку текста и сообщает, была ли она изменена.
def fix_line(line: str) -> tuple[str, bool, bool]:
    if not has_suspect_text(line):
        return line, False, False

    best = line
    best_score = text_score(line)

    for candidate in candidate_variants(line):
        score = text_score(candidate)
        if score > best_score:
            best = candidate
            best_score = score

    changed = best != line
    unresolved = "???" in best
    return best, changed, unresolved


# Исправляет все строки текста и возвращает статистику изменений.
def fix_text(text: str) -> tuple[str, int, list[int]]:
    changed_lines = 0
    unresolved_lines: list[int] = []
    fixed_lines: list[str] = []

    for line_number, line in enumerate(text.splitlines(keepends=True), 1):
        newline = ""
        content = line
        if line.endswith("\r\n"):
            newline = "\r\n"
            content = line[:-2]
        elif line.endswith("\n"):
            newline = "\n"
            content = line[:-1]

        fixed, changed, unresolved = fix_line(content)
        if changed:
            changed_lines += 1
        if unresolved:
            unresolved_lines.append(line_number)

        fixed_lines.append(fixed + newline)

    return "".join(fixed_lines), changed_lines, unresolved_lines


# Ищет подходящие текстовые файлы в указанной корневой папке.
def iter_text_files(root: Path) -> list[Path]:
    paths: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.name == "fix.py":
            continue
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        paths.append(path)
    return paths


# Исправляет один файл на диске и при необходимости создает backup.
def process_file(path: Path, write: bool, backup: bool) -> tuple[bool, int, list[int]]:
    try:
        original = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return False, 0, []

    fixed, changed_lines, unresolved_lines = fix_text(original)
    if changed_lines == 0:
        return False, 0, unresolved_lines

    if write:
        if backup:
            backup_path = path.with_suffix(path.suffix + ".bak")
            if not backup_path.exists():
                backup_path.write_text(original, encoding="utf-8")
        path.write_text(fixed, encoding="utf-8", newline="")

    return True, changed_lines, unresolved_lines


# Разбирает аргументы CLI и запускает сценарий исправления кодировки.
def main() -> int:
    parser = argparse.ArgumentParser(
        description="Исправляет типичные крокозябры после неверной перекодировки и сохраняет файлы в UTF-8."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Только показать, что будет исправлено, без записи в файлы.",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Не создавать .bak-копии перед записью.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=["."],
        help="Файлы или папки для обработки. По умолчанию весь проект.",
    )
    args = parser.parse_args()

    targets: list[Path] = []
    for raw in args.paths:
        path = Path(raw)
        if path.is_file():
            targets.append(path)
        elif path.is_dir():
            targets.extend(iter_text_files(path))

    unique_targets = sorted({path.resolve() for path in targets})

    changed_files = 0
    changed_lines_total = 0
    unresolved_hits: list[tuple[Path, int]] = []

    for path in unique_targets:
        changed, changed_lines, unresolved_lines = process_file(
            path=path,
            write=not args.check,
            backup=not args.no_backup,
        )
        if changed:
            changed_files += 1
            changed_lines_total += changed_lines
            status = "would fix" if args.check else "fixed"
            print(f"{status}: {path} ({changed_lines} lines)")
        if unresolved_lines:
            unresolved_hits.extend((path, line_number) for line_number in unresolved_lines)

    if args.check:
        print(f"check complete: {changed_files} files, {changed_lines_total} lines would change")
    else:
        print(f"done: {changed_files} files, {changed_lines_total} lines changed")

    if unresolved_hits:
        print(f"warning: {len(unresolved_hits)} lines still contain '???' and may need manual repair")
        for path, line_number in unresolved_hits[:20]:
            print(f"unresolved: {path}:{line_number}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
