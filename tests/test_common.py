from pathlib import Path
from unittest.mock import MagicMock

import pytest

from jellyfin_media_renamer.common import infer_name_and_year


@pytest.mark.parametrize(
    ("path", "expected_raw_name", "expected_name", "expected_year"),
    [
        ("./Milo", "Milo", "Milo", None),
        ("./[AC] Kamisama Kiss", "Kamisama Kiss", "Kamisama Kiss", None),
        (
            "./Harry Potter and the Chamber of Secrets (2002) [1080p]",
            "Harry Potter and the Chamber of Secrets (2002)",
            "Harry Potter and the Chamber of Secrets",
            2002,
        ),
        (
            "./My Little Pony Equestria Girls - Friendship Games (2015) [1080p] [BluRay] [5.1] [YTS.MX]",
            "My Little Pony Equestria Girls - Friendship Games (2015)",
            "My Little Pony Equestria Girls - Friendship Games",
            2015,
        ),
        (
            "./My.Little.Pony.Equestria.Girls.2013.1080p.BluRay.x264-PHOBOS[rarbg]",
            "My.Little.Pony.Equestria.Girls.2013.1080p.BluRay.x264-PHOBOS",
            "My Little Pony Equestria Girls",
            2013,
        ),
        (
            "./Harry Potter and the Deathly Hallows Part 2 (2011) 1080p.BRrip.scOrp.sujaidr (pimprg)",
            "Harry Potter and the Deathly Hallows Part 2 (2011) 1080p.BRrip.scOrp.sujaidr (pimprg)",
            "Harry Potter and the Deathly Hallows Part 2",
            2011,
        ),
        (
            "./Ouran High School Host Club (2006) [1080p x265 HEVC 10bit BluRay Dual Audio AAC] [Prof][darkflux fixed]",
            "Ouran High School Host Club (2006)",
            "Ouran High School Host Club",
            2006,
        ),
        (
            "./Malcolm in the Middle (2000) (1080p AMZN WEB-DL x265 Silence)",
            "Malcolm in the Middle (2000) (1080p AMZN WEB-DL x265 Silence)",
            "Malcolm in the Middle",
            2000,
        ),
        (
            "./[Erai-raws] Death Note [1080p][Multiple Subtitle][BCE68CE7]",
            "Death Note",
            "Death Note",
            None,
        ),
        (
            "./www.UIndex.org    -    Nacho Libre 2006 1080p ATVP WEB-DL DD 5 1 H 264-PiRaTeS",
            "www.UIndex.org    -    Nacho Libre 2006 1080p ATVP WEB-DL DD 5 1 H 264-PiRaTeS",
            "Nacho Libre",
            2006,
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
