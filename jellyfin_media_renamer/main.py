import enum
import os
import re
import sys
from pathlib import Path

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


class InputType(str, enum.Enum):
    FOLDER_WITH_MOVIE = "movie in folder"
    MOVIE_WITHOUT_FOLDER = "movie without folder"
    FOLDER_WITH_SHOW_SEASONS = "show"


def infer_input_type(fp: Path) -> InputType:
    if fp.is_file():
        if fp.suffixes and (fp.suffixes[-1][1:] in VIDEO_FILE_EXTS):
            return InputType.MOVIE_WITHOUT_FOLDER

        raise CommandError(f"Unknown file extension: {fp.suffix}")

    sub_objs = list(fp.iterdir())

    if any(
        sub_obj.is_dir() and "SEASON" in sub_obj.name.upper() for sub_obj in sub_objs
    ):
        return InputType.FOLDER_WITH_SHOW_SEASONS

    if any(
        sub_obj.is_file()
        and sub_obj.suffixes
        and sub_obj.suffixes[-1][1:].lower() in VIDEO_FILE_EXTS
        for sub_obj in sub_objs
    ):
        return InputType.FOLDER_WITH_MOVIE

    raise CommandError(f"Failed to determine MediaType for path: {fp}")


def process_movie_without_folder(fp: Path, name: str, year: int, new_stem: str):
    folder = fp.parent / new_stem
    folder.mkdir()
    fp.rename(folder / fp.with_name(new_stem).with_suffix(fp.suffixes[-1]).name)


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


def process_movie_inside_folder(fp: Path, name: str, year: int, new_stem: str):
    fp = fp.rename(fp.with_name(new_stem))

    sub_objs = {f for f in fp.iterdir() if f.is_file()}
    video_files = {
        f for f in sub_objs if f.suffixes and f.suffixes[-1][1:] in VIDEO_FILE_EXTS
    }
    subtitle_files = {
        f for f in sub_objs if f.suffixes and f.suffixes[-1][1:] in SUBTITLES_FILE_EXTS
    }

    if unprocessable_paths := (sub_objs - video_files - subtitle_files):
        print(
            "Unprocessable paths:\n",
            "\n".join(f"\t{f}" for f in unprocessable_paths),
            "\n",
        )

    assert len(video_files) >= 1

    # Sometimes torrents include a preview or some message from the uploader
    primary_video_file: Path | None = None
    if len(video_files) == 1:
        primary_video_file = next(iter(video_files))
    else:
        for file in video_files:
            _, test_name, _ = infer_name_and_year(file)
            if test_name.upper() == name.upper():
                primary_video_file = file
                break

    if primary_video_file is None:
        raise CommandError(f"Unable to determine movie file inside path: {fp}")

    primary_video_file.rename(
        primary_video_file.with_name(new_stem).with_suffix(
            primary_video_file.suffixes[-1]
        )
    )

    primary_subtitles_file: Path | None = None
    if len(subtitle_files) == 1:
        primary_subtitles_file = next(iter(subtitle_files))
    else:
        for file in subtitle_files:
            _, test_name, _ = infer_name_and_year(file)
            if test_name.upper() == name.upper():
                primary_subtitles_file = file
                break

    if primary_subtitles_file:
        primary_subtitles_file.rename(
            primary_subtitles_file.with_name(new_stem).with_suffix(
                "."
                + ".".join(
                    [s.removeprefix(".") for s in primary_subtitles_file.suffixes]
                )
            )
        )
    elif len(subtitle_files):
        print("Couldn't determine primary subtitles file :/")

    purge_extra_files(fp)


def infer_episode_number_and_name(
    fp: Path, raw_show_name: str, show_name: str, year: int, season: int
) -> tuple[int, str | None]:
    assert fp.is_file()

    re_patterns = [
        (r"episode\s(\d+)", 1),  # Episode 01
        (r"S\d{1,2}E(\d{1,3})", 1),  # S01E01
        (r"ep(\d{1,3})", 1),  # Ep01
        (rf"{season}x(\d{{1,3}})(?:\s|$|\.|\[|\(|\,|_)", 1),  # {season}x01
        (rf"(?:^|\s|\.){season}(\d{{2,3}})(?:\s|\.|$|_|-)", 1),  # {season}01
        (r"(?:^|\s|\.|_|-)((?:0\d)|(?:[1-9]\d))(?:\s|\.|$|_|-)", 1),  # 01
    ]

    ep_number: int | None = None
    match: re.Match[str] | None = None
    for pattern, cap_group in re_patterns:
        if match := next(re.finditer(pattern, fp.name, re.IGNORECASE), None):
            ep_number = int(match.group(cap_group).strip())
            break

    if ep_number is None:
        raise CommandError(f"Unable to determine episode number for path {fp}")

    name = fp.name[: -len(fp.suffix)].replace(raw_show_name, "").replace(show_name, "").strip()
    name = strip_tags(name)
    name = name.replace(match.group(), '', 1)  # Remove ep number

    for re_pattern in [
        r'((?:\(|\[|\s|-|\.)\d{4}(?:\)|\]|\s|-|\.))',  # Year
        r'(?:^|\s|\.|-|_)(ep|episode)(?:$|\s|\.|-|_)',  # ep | episode
        r'(\((?:(?:1080)|(?:480)|(?:720)|(?:2160))p.*\))',  # (1080p ...)
    ]:
        name = re.sub(re_pattern, "", name, re.IGNORECASE)

    name = name.strip(',.-_ ')

    return ep_number, name or None


def process_show_season(folder: Path, show_name: str, year: int):
    ...

    purge_extra_files(folder)


def process_show(fp: Path, raw_name: str, name: str, year: int, new_stem: str):
    fp = fp.rename(fp.with_name(new_stem))

    for file in fp.iterdir():
        if file.is_dir() and "SEASON" in file.name.upper():
            season_num = next(re.finditer(r"(\d{1,2})\s|$", file.name), None)
            if season_num is None:
                raise CommandError(f"Unable to determine season number for {file}")
            season_num = int(season_num.group(1))

            season_folder = file.rename(file.with_name(f"Season {season_num:02d}"))
            process_show_season(season_folder, name, year)


def main():
    raw_path = " ".join(sys.argv[1:])

    if not raw_path:
        raise CommandError("Please specify a path to a movie or show")

    fp = Path(raw_path)

    if not fp.exists():
        raise CommandError(f"No file or folder found for path: {fp}")

    input_type = infer_input_type(fp)
    print(f"Processing {input_type} at {fp.absolute()} ...")

    raw_name, name, year = get_name_and_year(fp)

    new_stem = name
    if year:
        new_stem += f" ({year})"

    if input_type == InputType.MOVIE_WITHOUT_FOLDER:
        process_movie_without_folder(fp, name, year, new_stem)

    if input_type == InputType.FOLDER_WITH_MOVIE:
        process_movie_inside_folder(fp, name, year, new_stem)

    if input_type == InputType.FOLDER_WITH_SHOW_SEASONS:
        process_show(fp, raw_name, name, year, new_stem)

    print("Done!")


if __name__ == "__main__":
    try:
        main()
    except CommandError as e:
        print(e.message)
        sys.exit(1)
