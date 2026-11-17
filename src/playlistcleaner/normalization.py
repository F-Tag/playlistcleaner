import re
from unicodedata import normalize

LIVE_ALBUM_PATTERN = "come along|live"
LIVE_TITLE_PATTERN = "live|ライブ"
INSTRUMENTAL_PATTERN = "instrumental|without|backing|karaoke|inst|カラオケ|off vocal|vocalless|ヴォーカルレス"
ALTERNATE_VERSION_PATTERN = (
    "tv|short|single|remix|mix|wo|edit|ver|style|another|version|recording|"
    "ヴァージョン|reprise|バージョン|mode"
)
REMASTER_PATTERN = "remaster|aufwachen"

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
