import os
from pathlib import Path
import re

VIDEO_FILE_EXTS = [
    "mkv",
    "mp4",
    "webm",
    "vob",
    "ogv",
    "avi",
    "mov",
    "m4p",
    "m4v",
    "mpg",
    "mpv",
]

SUBTITLES_FILE_EXTS = ["srt", "sub"]


class CommandError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def get_name_and_year(fp: Path) -> tuple[str, str, int | None]:
    raw_name, name, year = infer_name_and_year(fp)

    print(f"Detected name: {name}")
    print(f"Detected year: {year}")
    is_correct = input("Is this correct? (Y/n): ")
    is_correct = is_correct.upper() in ["Y", "Yes", "Ye", ""]

    if not is_correct:
        return (
            input_str := input("Enter correct name: "),
            input_str,
            int(input("Enter year (optional): ") or 0) or None,
        )

    return raw_name, name.strip(), year


def strip_tags(text: str) -> str:
    return re.sub(
        r"(\[[a-zA-Z0-9\-_\+\.\s\$\#\@\!]+\])", "", text
    )  # Remove tags like [1080p]


def infer_name_and_year(fp: Path) -> tuple[str, str, int | None]:
    name = fp.name
    if fp.is_file():
        name = name[: -len(fp.suffix)]

    # Find the year and split the title by it (we don't care for tags/junk after the year)
    year = next(re.finditer(r"\(([0-9]{4})\)", fp.name), None)
    if year:
        name = name.split(year.group())[0]
        year = int(year.group(1))
    else:
        # Try and find the year if it's not in ()
        year = next(re.finditer(r"((19)|(20)[0-9]{2})", fp.name), None)
        if year:
            year = year.group()
        if year:
            name = name.split(f".{year}")[0]
            year = int(year)

    raw_name = strip_tags(name).strip()

    name = re.sub(r"\.+(\w+)", r" \1", name)  # Replace dots with spaces
    name = strip_tags(name)

    return raw_name, name.strip(), year


def purge_extra_files(folder: Path):
    known_exts = {f".{ext}" for ext in [*VIDEO_FILE_EXTS, *SUBTITLES_FILE_EXTS]}
    extra_files = [
        f for f in folder.iterdir() if f.is_file() and f.suffix not in known_exts
    ]

    if not extra_files:
        return

    print("Purge extra files?\n", "\n".join(f"\t{f}" for f in extra_files), "\n")

    if input("[Y/n]: ").upper() in ["Y", "YES", "YE", ""]:
        for file in extra_files:
            os.remove(file.absolute())
