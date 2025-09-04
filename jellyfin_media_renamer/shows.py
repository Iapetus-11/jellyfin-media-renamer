import re
from pathlib import Path

from jellyfin_media_renamer.common import (
    CommandError,
    purge_extra_files,
    strip_tags,
    VIDEO_FILE_EXTS,
)


def infer_episode_number_and_name(
    fp: Path,
    raw_show_name: str,
    show_name: str,
    year: int | None,
    season: int,
) -> tuple[int, str | None]:
    assert fp.is_file()

    re_patterns = [
        (r"episode\s(\d+)", 1),  # Episode 01
        (r"S\d{1,2}E(\d{1,3})", 1),  # S01E01
        (r"ep(\d{1,3})", 1),  # Ep01
        (rf"{season}x(\d{{1,3}})(?:\s|$|\.|\[|\(|\,|_|-)", 1),  # {season}x01
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

    name = fp.name[: -len(fp.suffix)]
    name = re.sub(re.escape(raw_show_name), "", name, flags=re.IGNORECASE)
    name = re.sub(re.escape(show_name), "", name, flags=re.IGNORECASE)
    name = strip_tags(name.strip())
    if not match.group().isnumeric():
        name = name.replace(match.group(), "", 1)  # Remove ep number

    for re_pattern in [
        r"((?:\(|\[|\s|-|\.)\d{4}(?:\)|\]|\s|-|\.))",  # Year
        r"(\((?:(?:1080)|(?:480)|(?:720)|(?:2160))p.*\))",  # (1080p ...)
    ]:
        name = re.sub(re_pattern, "", name, count=1, flags=re.IGNORECASE)

    if "1080p " in name:
        name = name.split("1080p")[0]

    name = name.strip(",.-_ ")

    return ep_number, name or None


def process_show_season(
    folder: Path, raw_show_name: str, show_name: str, year: int | None, season: int
):
    show_stem = show_name
    if year:
        show_stem += f" ({year})"

    for fp in folder.iterdir():
        if not fp.is_file():
            print(f"Unknown folder/object: {fp}")
            continue

        if fp.suffixes[-1].removeprefix(".").lower() not in VIDEO_FILE_EXTS:
            continue

        ep_number, ep_name = infer_episode_number_and_name(
            fp,
            raw_show_name,
            show_name,
            year,
            season,
        )

        fp.rename(
            fp.with_name(
                f"{show_stem} S{season:02d}E{ep_number:02d} {ep_name or ''}".strip()
            ).with_suffix(fp.suffixes[-1])
        )

    purge_extra_files(folder)


def process_show(fp: Path, raw_name: str, name: str, year: int | None, new_stem: str):
    fp = fp.rename(fp.with_name(new_stem))

    for file in fp.iterdir():
        if file.is_dir() and "SEASON" in file.name.upper():
            season_num = next(re.finditer(r"(\d{1,2})(?:\s|$)", file.name), None)
            if season_num is None:
                raise CommandError(f"Unable to determine season number for {file}")
            season_num = int(season_num.group())

            season_folder = file.rename(file.with_name(f"Season {season_num:02d}"))
            process_show_season(season_folder, raw_name, name, year, season_num)
