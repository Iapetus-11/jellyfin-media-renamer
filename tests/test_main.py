from pathlib import Path
from unittest.mock import MagicMock

import pytest

from jellyfin_media_renamer.main import infer_episode_number_and_name, infer_input_type, infer_name_and_year, InputType


@pytest.mark.parametrize(
    ("path", "expected_raw_name", "expected_name", "expected_year"),
    [
        ("./Milo", "Milo", "Milo", None),
        ("./[AC] Kamisama Kiss", "Kamisama Kiss", "Kamisama Kiss", None),
        (
            "./Harry Potter and the Chamber of Secrets (2002) [1080p]",
            "Harry Potter and the Chamber of Secrets",
            "Harry Potter and the Chamber of Secrets",
            2002,
        ),
        (
            "./My Little Pony Equestria Girls - Friendship Games (2015) [1080p] [BluRay] [5.1] [YTS.MX]",
            "My Little Pony Equestria Girls - Friendship Games",
            "My Little Pony Equestria Girls - Friendship Games",
            2015,
        ),
        (
            "./My.Little.Pony.Equestria.Girls.2013.1080p.BluRay.x264-PHOBOS[rarbg]",
            "My.Little.Pony.Equestria.Girls",
            "My Little Pony Equestria Girls",
            2013,
        ),
        (
            "./Harry Potter and the Deathly Hallows Part 2 (2011) 1080p.BRrip.scOrp.sujaidr (pimprg)",
            "Harry Potter and the Deathly Hallows Part 2",
            "Harry Potter and the Deathly Hallows Part 2",
            2011,
        ),
        (
            "./Ouran High School Host Club (2006) [1080p x265 HEVC 10bit BluRay Dual Audio AAC] [Prof][darkflux fixed]",
            "Ouran High School Host Club",
            "Ouran High School Host Club",
            2006,
        ),
        (
            "./Malcolm in the Middle (2000) (1080p AMZN WEB-DL x265 Silence)",
            "Malcolm in the Middle",
            "Malcolm in the Middle",
            2000,
        ),
        (
            "./[Erai-raws] Death Note [1080p][Multiple Subtitle][BCE68CE7]",
            "Death Note",
            "Death Note",
            None,
        )
    ],
)
@pytest.mark.parametrize("is_file", [True, False])
def test_infer_name_and_year(
    is_file, path, expected_raw_name, expected_name, expected_year
):
    def make_path_mock(path_str: str) -> MagicMock:
        if is_file:
            path_str += ".mkv"

        path = Path(path_str)

        mock = MagicMock(spec=path)
        mock.is_file.return_value = is_file
        mock.suffix = path.suffix
        mock.name = path.name

        return mock

    raw_name, name, year = infer_name_and_year(make_path_mock(path))

    assert raw_name == expected_raw_name
    assert name == expected_name
    assert year == expected_year


@pytest.mark.parametrize(
    (
        "show_path",
        "path",
        "season",
        "expected_ep_number",
        "expected_ep_name",
    ),
    [
        (
            "The Suite Life of Zack and Cody/",
            "The Suite Life of Zack and Cody - 1x01 - Hotel Hangout.mkv",
            1,
            1,
            "Hotel Hangout",
        ),
        (
            "[Erai-raws] Death Note [1080p][Multiple Subtitle][BCE68CE7]/",
            "[Erai-raws] Death Note - 01 [1080p][Multiple Subtitle][BCE68CE7].mkv",
            0,
            1,
            None,
        ),
        (
            "Death Note 1080p Hybrid ITA BDRip DTS-HD-MA 2.0 Kira [SEV]/",
            "Death Note - Episode 01 - 1,28 1080p Hybrid ITA BDRip DTS-HD-MA 2.0 Kira [SEV].mkv",
            0,
            1,
            "1,28",
        ),
        (
            "Malcolm in the Middle (2000) (1080p AMZN WEB-DL x265 Silence)/",
            "Malcolm in the Middle (2000) - S07E22 - Graduation (1080p AMZN WEB-DL x265 Silence).mkv",
            7,
            22,
            "Graduation",
        ),
        (
            "Test Show/",
            "Test Show S01E01.mkv",
            1,
            1,
            None,
        ),
        (
            "Test Show/",
            "Test Show S01E01 Episode Name.mkv",
            1,
            1,
            "Episode Name",
        ),
        (
            "Test Show (2025)/",
            "Test Show (2025) S01E01 Episode Name.mkv",
            1,
            1,
            "Episode Name",
        ),
        (
            "Test Show (2025)/",
            "Test Show (2025) - S01E01 - Episode Name.mkv",
            1,
            1,
            "Episode Name",
        ),
        (
            "[Exiled-Destiny]_Maid-Sama!/",
            "[Exiled-Destiny]_Maid-Sama!_Ep16v2_(A46BDC49).mkv",
            0,
            16,
            None,
        ),
        (
            "One-Punch Man/",
            "One-Punch Man - 08 [BDRip 1080p AVC][FLAC].mkv",
            1,
            8,
            None,
        ),
        (
            "Invincible/",
            "S01E01-I'm Used to It [28559867].mkv",
            1,
            1,
            "I'm Used to It",
        ),
        (
            "NCIS (1234)/",
            "NCIS S01E01 Yankee White.mkv",
            1,
            1,
            "Yankee White",
        ),
        (
            "Naruto Shippuden/",
            "[Koten_Gars] Naruto Shippuden - 154 [iTunes][h.264][1080p][AC3] [A5D2B724].mkv",
            1,
            54,
            None,
        ),
        (
            "Invincible (2021)/",
            "Invincible (2021) - S01E02 - Here Goes Nothing (1080p WEB-DL x265 SAMPA).mkv",
            1,
            2,
            "Here Goes Nothing",
        ),
        (
            "./[AC] Kamisama Kiss/",
            "[AC] Kamisama Kiss - 04 [BD][1080p-Hi10][FLAC][Dual-Audio][1231231].mkv",
            1,
            4,
            None,
        )
    ],
)
def test_infer_episode_number_and_name(
    show_path, path, season, expected_ep_number, expected_ep_name
):
    def make_path_mock(str_path: str) -> MagicMock:
        path = Path(str_path)

        mock = MagicMock(spec=path)
        mock.is_file.return_value = not str_path.endswith('/')
        mock.suffix = path.suffix
        mock.name = path.name

        return mock

    raw_show_name, show_name, show_year = infer_name_and_year(make_path_mock(show_path))

    ep_number, ep_name = infer_episode_number_and_name(
        make_path_mock(path),
        raw_show_name,
        show_name,
        show_year,
        season,
    )

    assert ep_number == expected_ep_number
    assert ep_name == expected_ep_name


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
