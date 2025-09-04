from collections import Counter
import re
from pathlib import Path

from jellyfin_media_renamer.common import CommandError, purge_extra_files, strip_tags


def infer_episode_number_and_name(
    fp: Path, raw_show_name: str, show_name: str, year: int, season: int, duplicate_tokens: list[str],
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

    name = (
        fp.name[: -len(fp.suffix)]
        .replace(raw_show_name, "")
        .replace(show_name, "")
        .strip()
    )
    name = strip_tags(name)
    name = name.replace(match.group(), "", 1)  # Remove ep number

    for re_pattern in [
        r"((?:\(|\[|\s|-|\.)\d{4}(?:\)|\]|\s|-|\.))",  # Year
        r"(?:^|\s|\.|-|_)(ep|episode)(?:$|\s|\.|-|_)",  # ep | episode
        r"(\((?:(?:1080)|(?:480)|(?:720)|(?:2160))p.*\))",  # (1080p ...)
    ]:
        name = re.sub(re_pattern, "", name, flags=re.IGNORECASE)

    for duplicate_token in duplicate_tokens:
        name = name.replace(duplicate_token, '')

    name = name.strip(",.-_ ")

    return ep_number, name or None


def get_episode_name_duplicate_tokens(season_folder: Path) -> list[str]:
    DELIMITERS = [" ", ".", "_", "-"]

    tokens: Counter[str] = Counter()
    file_count = 0

    for fp in season_folder.iterdir():
        if fp.is_file():
            file_count += 1

            for delimiter in DELIMITERS:
                tokens.update(
                    [
                        p
                        for p in fp.name[: -len(fp.suffix)].split(delimiter)
                        if len(p) >= 3
                    ]
                )

    # If 90% of the episodes have the same token, then we can remove that token when trying to figure out episode names!
    duplicate_tokens = [
        token for token, count in tokens.items() if (count / file_count) >= 0.9
    ]

    return duplicate_tokens


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
