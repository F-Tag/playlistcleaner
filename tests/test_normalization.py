import re

import pytest

from playlistcleaner.normalization import (
    ALTERNATE_VERSION_PATTERN,
    INSTRUMENTAL_PATTERN,
    LIVE_ALBUM_PATTERN,
    LIVE_TITLE_PATTERN,
    REMASTER_PATTERN,
    normalize_text,
    simplify_title,
)


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


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("live", True),
        ("song [live]", True),
        ("ライブ", True),
        ("曲名ライブ版", True),
        ("olive", False),
        ("alive", False),
        ("delivery", False),
        ("outlive", False),
    ],
)
def test_live_title_pattern_requires_token_boundaries(
    value: str, expected: bool
) -> None:
    assert bool(re.search(LIVE_TITLE_PATTERN, value)) is expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("come along", True),
        ("come along 3", True),
        ("live album", True),
        ("olive", False),
        ("delivery", False),
    ],
)
def test_live_album_pattern_requires_token_boundaries(
    value: str, expected: bool
) -> None:
    assert bool(re.search(LIVE_ALBUM_PATTERN, value)) is expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("instrumental", True),
        ("instrumentals", True),
        ("song inst", True),
        ("song inst.", True),
        ("karaoke", True),
        ("off vocal", True),
        ("without vocals", True),
        ("without vocal", True),
        ("backing track", True),
        ("vocalless", True),
        ("1982カラオケ", True),
        ("ヴォーカルレス", True),
        ("instant crush", False),
        ("without you", False),
        ("backing", False),
    ],
)
def test_instrumental_pattern_requires_token_boundaries(
    value: str, expected: bool
) -> None:
    assert bool(re.search(INSTRUMENTAL_PATTERN, value)) is expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("tv size", True),
        ("tv用インスト", True),
        ("short version", True),
        ("single", True),
        ("singles", True),
        ("remix", True),
        ("remixes", True),
        ("1st mix", True),
        ("another version", True),
        ("edited version", True),
        ("master ver.", True),
        ("1982ヴァージョン", True),
        ("バージョン", True),
        ("every night", False),
        ("forever mine", False),
        ("never grow old", False),
        ("overture", False),
        ("joy to the world", False),
        ("please let me wonder", False),
        ("secret lover", False),
        ("edition", False),
        ("model", False),
    ],
)
def test_alternate_version_pattern_requires_token_boundaries(
    value: str, expected: bool
) -> None:
    assert bool(re.search(ALTERNATE_VERSION_PATTERN, value)) is expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("remaster", True),
        ("remastered", True),
        ("2020 remaster", True),
        ("aufwachen", True),
        ("premaster", False),
        ("remastering", False),
    ],
)
def test_remaster_pattern_requires_token_boundaries(value: str, expected: bool) -> None:
    assert bool(re.search(REMASTER_PATTERN, value)) is expected
