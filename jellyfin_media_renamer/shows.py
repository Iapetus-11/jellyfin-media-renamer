import re
from dataclasses import dataclass
from pathlib import Path

from jellyfin_media_renamer.common import (
    CommandError,
    purge_extra_files,
    strip_tags,
    VIDEO_FILE_EXTS,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class EpisodeInfo:
    number: int
    name: str | None
    parts: str | None


def infer_episode_info(
    fp: Path,
    raw_show_name: str,
    show_name: str,
    year: int | None,
    season: int,
) -> EpisodeInfo:
    assert fp.is_file()

    ep_number_patterns = [
        r"episode\s(?P<ep>\d+)",  # Episode 01
        r"S\d{1,2}E((?P<ep>\d{1,3})(?P<parts>(?:abcd)|(?:abc)|(?:ab)|(?:a))?)(?:\s|-|$|_|\.|\()",  # S01E01 or # S01E01
        r"ep(?P<ep>\d{1,3})",  # Ep01
        rf"{season}x(?P<ep>\d{{1,3}})(?:\s|$|\.|\[|\(|\,|_|-)",  # {season}x01
        rf"(?:^|\s|\.){season}(?P<ep>\d{{2,3}})(?:\s|\.|$|_|-)",  # {season}01
        r"(?:^|\s|\.|_|-)(?P<ep>(?:0\d)|(?:[1-9]\d))(?:\s|\.|$|_|-)",  # 01
    ]

    ep_number: int | None = None
    parts: str | None = None

    match: re.Match[str] | None = None
    for pattern in ep_number_patterns:
        if match := next(re.finditer(pattern, fp.name, re.IGNORECASE), None):
            ep_number = int(match.group("ep").strip())

            try:
                parts = (match.group("parts") or "").strip()
            except IndexError:
                pass

            break

    if ep_number is None:
        raise CommandError(f"Unable to determine episode number for path {fp}")

    ep_part_patterns = [
        r"(?:(?:parts)|(?:part)|(?:pt))(?:\s|\.|-|_)*(?P<p_start>[a-dA-D1-9])(?:-(?P<p_end>[a-dA-D1-9]))?(?:\s|\.|-|_|$)",
    ]

    for pattern in ep_part_patterns:
        if part_match := next(re.finditer(pattern, fp.name, re.IGNORECASE), None):
            part_match_dict = part_match.groupdict()
            parts = "-".join(filter(None, map(str.strip, [
                part_match_dict.get("p_start", ""),
                part_match_dict.get("p_end", ""),
            ])))

    name = fp.name[: -len(fp.suffix)]
    name = re.sub(re.escape(raw_show_name), "", name, flags=re.IGNORECASE)
    name = re.sub(re.escape(show_name), "", name, flags=re.IGNORECASE)
    name = strip_tags(name.strip())
    full_group = match.group().rstrip('. ')
    if not full_group.isnumeric():
        name = name.replace(full_group, "", 1)  # Remove ep number

    for re_pattern in [
        r"((?:\(|\[|\s|-|\.)\d{4}(?:\)|\]|\s|-|\.))",  # Year
        r"(\((?:(?:1080)|(?:480)|(?:720)|(?:2160))p.*\))",  # (1080p ...)
        r"((?:www)?\.?UIndex\.org\s*-?\s*)",  # www.UIndex.org -
        r"((?:-|_|\.|\s)?WEB(?:-|_|\.|\s)DL(?:-|_|\.|\s)?)"  # WEB-Dl
        r"((?:-|_|\.|\s)?DVD(?:-|_|\.|\s)?RIP(?:-|_|\.|\s)?)",  # DVDRIP
    ]:
        name = re.sub(re_pattern, "", name, count=1, flags=re.IGNORECASE)

    for resolution in ("720p", "1080p", "2160p"):
        if f"{resolution} " in name:
            name = name.split(resolution)[0]
            break

    name = name.strip(",.-_ ")
    parts = (parts or '').strip(",.-_ ")

    if not (parts.isalpha() or parts.isnumeric()):
        parts = None

    return EpisodeInfo(
        number=ep_number,
        name=name or None,
        parts=parts or None,
    )


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

        ep_info = infer_episode_info(
            fp,
            raw_show_name,
            show_name,
            year,
            season,
        )

        new_name = f"{show_stem} S{season:02d}E{ep_info.number:02d}"

        if ep_info.name:
            new_name += ' ' + ep_info.name
            new_name = new_name.strip()

        # TODO: Not really sure what to do with parts yet...
        # if ep_info.parts:
        #     p_min = min(ep_info.parts)
        #     p_max = max(ep_info.parts)
        #
        #     if p_min == p_max:
        #         new_name += f'-part{p_min}'
        #     else:
        #         new_name += f'-part{p_min}-{p_max}'

        fp.rename(
            fp.with_name(new_name.strip()).with_suffix(fp.suffixes[-1])
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
