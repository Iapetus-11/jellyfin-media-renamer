import dataclasses
import enum
import logging
import sys
from pathlib import Path

from jellyfin_media_renamer.common import (
    VIDEO_FILE_EXTS,
    CommandError,
    get_name_and_year,
)
from jellyfin_media_renamer.movies import (
    process_movie_inside_folder,
    process_movie_without_folder,
)
from jellyfin_media_renamer.shows import process_show

logger = logging.getLogger(__name__)


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class CLIFlags:
    verbose: bool


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
        sub_obj.is_dir()
        and ("SEASON" in sub_obj.name.upper() or "S0" in sub_obj.name.upper())
        for sub_obj in sub_objs
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


def setup_logging(*, verbose: bool):
    level = logging.INFO
    format_ = "%(message)s"

    if verbose:
        level = logging.DEBUG
        format_ = "{asctime} {levelname}: {message}"

    logging.basicConfig(
        level=level,
        style="{",
        format=format_,
        force=True,
    )


def parse_args() -> tuple[CLIFlags, str]:
    """Parses sys.argv, returning a tuple containing (parsed flags, target path)"""

    found_flags: set[str] = set()
    path = ""

    for arg in sys.argv[1:]:
        if arg.startswith("-"):
            found_flags.add(arg.casefold())
        elif path:
            raise CommandError(f"Unexpected argument: {arg!r}")
        else:
            path = arg

    flags = CLIFlags(
        verbose=("--verbose" in found_flags or "-v" in found_flags),
    )

    return flags, path


def main():
    flags, raw_path = parse_args()

    setup_logging(verbose=flags.verbose)

    if not raw_path:
        raise CommandError("Please specify a path to a movie or show")

    fp = Path(raw_path)

    if not fp.exists():
        raise CommandError(f"No file or folder found for path: {fp}")

    input_type = infer_input_type(fp)
    logger.info(f"Processing {input_type.value} at {fp.absolute()} ...")

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

    logger.info("Done!")


if __name__ == "__main__":
    try:
        main()
    except CommandError as e:
        logger.exception(e.message)
        sys.exit(1)
