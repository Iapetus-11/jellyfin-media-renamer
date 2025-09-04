from pathlib import Path
from unittest.mock import MagicMock

import pytest

from jellyfin_media_renamer.main import InputType, infer_input_type


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
