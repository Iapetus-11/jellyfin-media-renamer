import enum
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


def get_name_and_year(fp: Path) -> tuple[str, int | None]:
    name, year = infer_name_and_year(fp)

    print(f"Detected name: {name}")
    print(f"Detected year: {year}")
    is_correct = input("Is this correct? (Y/n): ")
    is_correct = is_correct.upper() in ["Y", "Yes", "Ye", ""]

    if not is_correct:
        return (
            input("Enter correct name: "),
            int(input("Enter year (optional): ") or 0) or None,
        )

    return name.strip(), year


def infer_name_and_year(fp: Path) -> tuple[str, int | None]:
    name = fp.name
    if fp.is_file():
        name = name[: len(fp.suffix)]

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

    name = re.sub(r"\.+(\w+)", r" \1", name)  # Replace dots with spaces
    name = re.sub(
        r"(\[[a-zA-Z0-9\-_\+\.\s\$\#\@\!]+\])", "", name
    )  # Remove tags like [1080p]

    return name.strip(), year


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


def main():
    raw_path = " ".join(sys.argv[1:])

    if not raw_path:
        raise CommandError("Please specify a path to a movie or show")

    fp = Path(raw_path)

    if not fp.exists():
        raise CommandError(f"No file or folder found for path: {fp}")

    input_type = infer_input_type(fp)
    print(f"Processing {input_type} at {fp.absolute()} ...")

    name, year = get_name_and_year(fp)

    new_stem = name
    if year:
        new_stem += f" ({year})"

    if input_type == InputType.MOVIE_WITHOUT_FOLDER:
        fp.rename(fp.with_name(new_stem).with_suffix(fp.suffixes[-1]))
        return

    if input_type == InputType.FOLDER_WITH_MOVIE:
        fp = fp.rename(fp.with_name(new_stem))

        sub_objs = {f for f in fp.iterdir() if f.is_file()}
        video_files = {
            f for f in sub_objs if f.suffixes and f.suffixes[-1][1:] in VIDEO_FILE_EXTS
        }
        subtitle_files = {
            f
            for f in sub_objs
            if f.suffixes and f.suffixes[-1][1:] in SUBTITLES_FILE_EXTS
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
                test_name, _ = infer_name_and_year(file)
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
                test_name, _ = infer_name_and_year(file)
                if test_name.upper() == name.upper():
                    primary_subtitles_file = file
                    break

        if primary_subtitles_file:
            primary_subtitles_file.rename(
                primary_subtitles_file.with_name(new_stem).with_suffix(
                    primary_subtitles_file.suffixes[-1]
                )
            )
        elif len(subtitle_files):
            print("Couldn't determine primary subtitles file :/")

        print('Done!')


if __name__ == "__main__":
    try:
        main()
    except CommandError as e:
        print(e.message)
        sys.exit(1)
