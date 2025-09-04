from pathlib import Path

from jellyfin_media_renamer.common import (
    SUBTITLES_FILE_EXTS,
    VIDEO_FILE_EXTS,
    CommandError,
    infer_name_and_year,
    purge_extra_files,
)


def process_movie_without_folder(fp: Path, name: str, year: int, new_stem: str):
    folder = fp.parent / new_stem
    folder.mkdir()
    fp.rename(folder / fp.with_name(new_stem).with_suffix(fp.suffixes[-1]).name)


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
