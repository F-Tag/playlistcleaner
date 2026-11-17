import pytest

from playlistcleaner.normalization import normalize_text, simplify_title


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
def test_normalize_text(value: str, expected: str) -> None:
    assert normalize_text(value) == expected


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        ("song (live)", "song"),
        ("song [remix]", "song"),
        ("song {edit}", "song"),
        ("song -tv size-", "song"),
        ("song ~short~", "song"),
        ("song", "song"),
    ],
)
def test_simplify_title(title: str, expected: str) -> None:
    assert simplify_title(title) == expected
