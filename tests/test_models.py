from playlistcleaner.models import Track


def test_track_tag_returns_value_or_none() -> None:
    track = Track(path="song.mp3", tags={"TITLE": "Song"})

    assert track.tag("TITLE") == "Song"
    assert track.tag("ARTIST") is None
