from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class Track:
    """プレイリスト内の1曲分のメタデータ。"""

    path: str
    tags: Mapping[str, str]

    def tag(self, name: str) -> str | None:
        return self.tags.get(name)
