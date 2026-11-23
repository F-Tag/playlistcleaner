import re
from unicodedata import normalize

_ASCII_WORD = "a-z0-9_"


def _token(pattern: str) -> str:
    """ASCII 英数字の語中一致を防ぐ前後の境界を付ける。

    対象の文字列は `normalize_text()` で小文字化済みであることを前提とする。
    この関数は ASCII のトークンにだけ使い、日本語のトークンには境界を付けない。
    """
    return rf"(?<![{_ASCII_WORD}])(?:{pattern})(?![{_ASCII_WORD}])"


LIVE_ALBUM_PATTERN = _token("come along|live")
LIVE_TITLE_PATTERN = f"{_token('live')}|ライブ"
INSTRUMENTAL_PATTERN = (
    f"{_token('instrumentals?|without vocals?|backing track|karaoke|inst|off vocal|vocalless')}"
    "|カラオケ|ヴォーカルレス"
)
ALTERNATE_VERSION_PATTERN = (
    f"{_token('tv|short|singles?|remix(?:es)?|mix(?:es)?|wo|edit(?:ed)?|ver|style|another|versions?|recordings?|reprise|mode')}"
    "|ヴァージョン|バージョン"
)
REMASTER_PATTERN = _token("remaster(?:ed)?|aufwachen")

_PUNCTUATION = re.compile("[\\/\\^$*+?.|'\"・,、。’]")
_SPACES = re.compile(" +")
_PARENTHESES = re.compile(r"\(.*?\)")
_BRACKETS = re.compile(r"\[.*?\]")
_BRACES = re.compile(r"{.*?}")
_DASHES = re.compile(r"\-.*?\-")
_TILDES = re.compile(r"\~.*?\~")


def normalize_text(value: str) -> str:
    """タグ比較用に文字列を正規化する。"""
    value = normalize("NFKC", value).lower()
    value = _PUNCTUATION.sub(" ", value)
    value = _SPACES.sub(" ", value)
    return value.strip(" ")


def simplify_title(title: str) -> str:
    """括弧書きやバージョン表記を除いた比較用タイトルを返す。"""
    for pattern in (_PARENTHESES, _BRACKETS, _BRACES, _DASHES, _TILDES):
        title = pattern.sub("", title)
    return title.replace("-", "").replace("~", "").replace(" ", "")
