import pytest

from playlistcleaner.cli import main, normalizer


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("Hello, World", "hello world"),
        ("ＡＢＣ　ＤＥＦ", "abc def"),
        ("  Multiple   Spaces  ", "multiple spaces"),
        ("foo・bar、baz", "foo bar baz"),
        ("Don't Stop", "don t stop"),
    ],
)
def test_normalizer(value: str, expected: str) -> None:
    assert normalizer(value) == expected


def test_main_requires_a_playlist_argument() -> None:
    with pytest.raises(SystemExit, match="usage: playlistcleaner"):
        main([])
