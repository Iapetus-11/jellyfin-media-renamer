from pathlib import Path
from unittest.mock import MagicMock

import pytest

from jellyfin_media_renamer.common import infer_name_and_year
from jellyfin_media_renamer.shows import infer_episode_info


@pytest.mark.parametrize(
    (
        "show_path",
        "path",
        "season",
        "expected_ep_numbers",
        "expected_ep_name",
        "expected_parts",
    ),
    [
        (
            "The Suite Life of Zack and Cody/",
            "The Suite Life of Zack and Cody - 1x01 - Hotel Hangout.mkv",
            1,
            [1],
            "Hotel Hangout",
            None,
        ),
        (
            "The Suite Life of Zack and Cody/",
            "The Suite Life Of Zack and Cody- 1x16- Big hair and Baseball.mkv",
            1,
            [16],
            "Big hair and Baseball",
            None,
        ),
        (
            "[Erai-raws] Death Note [1080p][Multiple Subtitle][BCE68CE7]/",
            "[Erai-raws] Death Note - 01 [1080p][Multiple Subtitle][BCE68CE7].mkv",
            0,
            [1],
            None,
            None,
        ),
        (
            "Death Note/",
            "Death Note - Episode 01 - 1,28 1080p Hybrid ITA BDRip DTS-HD-MA 2.0 Kira [SEV].mkv",
            0,
            [1],
            "1,28",
            None,
        ),
        (
            "Malcolm in the Middle (2000) (1080p AMZN WEB-DL x265 Silence)/",
            "Malcolm in the Middle (2000) - S07E22 - Graduation (1080p AMZN WEB-DL x265 Silence).mkv",
            7,
            [22],
            "Graduation",
            None,
        ),
        (
            "Test Show/",
            "Test Show S01E01.mkv",
            1,
            [1],
            None,
            None,
        ),
        (
            "Test Show/",
            "Test Show S01E01 Episode Name.mkv",
            1,
            [1],
            "Episode Name",
            None,
        ),
        (
            "Test Show (2025)/",
            "Test Show (2025) S01E01 Episode Name.mkv",
            1,
            [1],
            "Episode Name",
            None,
        ),
        (
            "Test Show (2025)/",
            "Test Show (2025) - S01E01 - Episode Name.mkv",
            1,
            [1],
            "Episode Name",
            None,
        ),
        (
            "[Exiled-Destiny]_Maid-Sama!/",
            "[Exiled-Destiny]_Maid-Sama!_Ep16v2_(A46BDC49).mkv",
            0,
            [16],
            "v2_(A46BDC49)",  # Not optimal :/
            None,
        ),
        (
            "One-Punch Man/",
            "One-Punch Man - 08 [BDRip 1080p AVC][FLAC].mkv",
            1,
            [8],
            None,
            None,
        ),
        (
            "Invincible/",
            "S01E01-I'm Used to It [28559867].mkv",
            1,
            [1],
            "I'm Used to It",
            None,
        ),
        (
            "NCIS (1234)/",
            "NCIS S01E01 Yankee White.mkv",
            1,
            [1],
            "Yankee White",
            None,
        ),
        (
            "Naruto Shippuden/",
            "[Koten_Gars] Naruto Shippuden - 154 [iTunes][h.264][1080p][AC3] [A5D2B724].mkv",
            1,
            [54],
            None,
            None,
        ),
        (
            "Invincible (2021)/",
            "Invincible (2021) - S01E02 - Here Goes Nothing (1080p WEB-DL x265 SAMPA).mkv",
            1,
            [2],
            "Here Goes Nothing",
            None,
        ),
        (
            "./[AC] Kamisama Kiss/",
            "[AC] Kamisama Kiss - 04 [BD][1080p-Hi10][FLAC][Dual-Audio][1231231].mkv",
            1,
            [4],
            None,
            None,
        ),
        (
            "./SpongeBob SquarePants/",
            "SpongeBob SquarePants S08E05ab - Squidward's School for Grown Ups + Oral Report (1080p AMZN Webrip x265 10bit EAC3 2.0 - Frys) [TAoE].mkv",
            8,
            [5],
            "Squidward's School for Grown Ups + Oral Report",
            "ab",
        ),
        (
            "./SpongeBob SquarePants/",
            "SpongeBob SquarePants S08E05a - Squidward's School for Grown Ups + Oral Report (1080p AMZN Webrip x265 10bit EAC3 2.0 - Frys) [TAoE].mkv",
            8,
            [5],
            "Squidward's School for Grown Ups + Oral Report",
            "a",
        ),
        (
            "./A Mickey Mouse Cartoon/",
            "S01E01. No Service - A Mickey Mouse Cartoon.mp4",
            1,
            [1],
            "No Service",
            None,
        ),
        (
            "./The Expanse/",
            "The Expanse S01E09E10.mp4",
            1,
            [9, 10],
            None,
            None,
        ),
        (
            "./The Office/",
            "E11 Night Out.mp4",
            None,
            [11],
            "Night Out",
            None,
        ),
        (
            "./Gilmore.Girls/",
            "Gilmore.Girls.S02E13.A-Tisket,.A-Tasket.1080p.WEB-DL.x265.10bit.HEVC-MONOLITH.mkv",
            2,
            [13],
            "A-Tisket, A-Tasket",
            None,
        ),
    ],
)
def test_infer_episode_info(
    show_path, path, season, expected_ep_numbers, expected_ep_name, expected_parts
):
    def make_path_mock(str_path: str) -> MagicMock:
        path = Path(str_path)

        mock = MagicMock(spec=path)
        mock.is_file.return_value = not str_path.endswith("/")
        mock.suffix = path.suffix
        mock.name = path.name

        return mock

    raw_show_name, show_name, show_year = infer_name_and_year(make_path_mock(show_path))

    info = infer_episode_info(
        make_path_mock(path),
        raw_show_name,
        show_name,
        show_year,
        season,
    )

    assert info.numbers == expected_ep_numbers
    assert info.name == expected_ep_name
    assert info.parts == expected_parts
