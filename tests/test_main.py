from pathlib import Path
from unittest.mock import MagicMock

import pytest

from jellyfin_media_renamer.main import infer_input_type, infer_name_and_year, InputType


@pytest.mark.parametrize(
    ("fp", "expected_name", "expected_year"),
    [
        (Path("./Milo"), "Milo", None),
        (Path("./[AC] Kamisama Kiss"), "Kamisama Kiss", None),
        (
            Path("./Harry Potter and the Chamber of Secrets (2002) [1080p]"),
            "Harry Potter and the Chamber of Secrets",
            2002,
        ),
        (
            Path(
                "./My Little Pony Equestria Girls - Friendship Games (2015) [1080p] [BluRay] [5.1] [YTS.MX]"
            ),
            "My Little Pony Equestria Girls - Friendship Games",
            2015,
        ),
        (
            Path(
                "./My.Little.Pony.Equestria.Girls.2013.1080p.BluRay.x264-PHOBOS[rarbg]"
            ),
            "My Little Pony Equestria Girls",
            2013,
        ),
        (
            Path(
                "./Harry Potter and the Deathly Hallows Part 2 (2011) 1080p.BRrip.scOrp.sujaidr (pimprg)"
            ),
            "Harry Potter and the Deathly Hallows Part 2",
            2011,
        ),
        (
            Path(
                "./Ouran High School Host Club (2006) [1080p x265 HEVC 10bit BluRay Dual Audio AAC] [Prof][darkflux fixed]"
            ),
            "Ouran High School Host Club",
            2006,
        ),
    ],
)
def test_infer_name_and_year(fp: Path, expected_name, expected_year):
    name, year = infer_name_and_year(fp)

    assert name == expected_name
    assert year == expected_year


@pytest.mark.parametrize(
    ("fp", "fp_items", "expected_type"),
    [
        (Path("./test.mp4"), [], InputType.MOVIE_WITHOUT_FOLDER),
        (Path("/path/to/my/movie.mkv"), [], InputType.MOVIE_WITHOUT_FOLDER),
        (
            Path("/path/to/movie"),
            ["movie.mkv", "movie.srt", "other.txt", "other/"],
            InputType.FOLDER_WITH_MOVIE,
        ),
        (
            Path("path/to/show"),
            ["Season 1/", "Season 02/", "balls.txt"],
            InputType.FOLDER_WITH_SHOW_SEASONS,
        ),
    ],
)
def test_infer_input_type(fp, fp_items, expected_type):
    def make_path_mock(path: str | Path, is_dir: bool) -> MagicMock:
        path = Path(path)
        mock = MagicMock(spec=path)
        mock.is_dir.return_value = is_dir
        mock.is_file.return_value = not is_dir
        mock.name = path.name
        mock.suffixes = path.suffixes

        return mock

    fp_mock = make_path_mock(fp, bool(fp_items))
    fp_mock.iterdir.return_value = (
        make_path_mock(sub_obj, is_dir=sub_obj.endswith("/")) for sub_obj in fp_items
    )

    assert infer_input_type(fp_mock) == expected_type
