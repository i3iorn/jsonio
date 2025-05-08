# test_source_classifier.py

import io
import re
import pytest
from pathlib import Path

from jsonio._utils import Flags, SourceType, SUPPORTED_NETWORK_PROTOCOLS
from jsonio._classifier import SourceClassifier  # adjust import if necessary


class Dummy:
    """Just to test non‐string, non‐bytes, non‐path with read()"""
    def read(self):
        return "dummy"


@pytest.mark.parametrize("flags, source, expected_type, expected_value", [
    # IS_JSON flag with valid string
    (Flags.IS_JSON, '{"key": "value"}', SourceType.JSON_STR, '{"key": "value"}'),
    # IS_PATH flag always yields a Path object
    (Flags.IS_PATH, "some/file.txt", SourceType.PATH, Path("some/file.txt")),
])
def test_explicit_flags(flags, source, expected_type, expected_value):
    typ, val = SourceClassifier.classify_source(source, flags)
    assert typ is expected_type
    assert val == expected_value


def test_is_json_flag_with_non_string():
    with pytest.raises(ValueError, match="IS_JSON flag but not a string"):
        SourceClassifier.classify_source(123, Flags.IS_JSON)


def test_none_source_raises():
    with pytest.raises(ValueError, match="Cannot read from None"):
        SourceClassifier.classify_source(None, Flags.NONE)


def test_url_detection():
    # pick a supported protocol prefix
    proto = SUPPORTED_NETWORK_PROTOCOLS[0]
    src = f"{proto}example.com/data.json"
    typ, val = SourceClassifier.classify_source(src, Flags.NONE)
    assert typ is SourceType.URL
    assert val == src


def test_bytes_and_bytearray():
    for b in (b'{"a":1}', bytearray(b'{"b":2}')):
        typ, val = SourceClassifier.classify_source(b, Flags.NONE)
        assert typ is SourceType.BYTES
        assert val == b


def test_file_like_object():
    stream = io.StringIO('{"x":10}')
    typ, val = SourceClassifier.classify_source(stream, Flags.NONE)
    assert typ is SourceType.STREAM
    assert val is stream

    # an arbitrary object with read()
    dummy = Dummy()
    typ2, val2 = SourceClassifier.classify_source(dummy, Flags.NONE)
    assert typ2 is SourceType.STREAM
    assert val2 is dummy


@pytest.mark.parametrize("path_str", [
    "data.json",            # extension .json
    "nested/dir/file.txt",  # safe regex
    "C:\\Users\\me\\a.cfg", # windows style
])
def test_safe_path_heuristic_matches(path_str, flags=None, tmp_path=None):
    # No flags => unsafe => falls back to safe => True => PATH
    typ, val = SourceClassifier.classify_source(path_str, Flags.NONE)
    assert typ is SourceType.PATH
    assert isinstance(val, Path)
    assert Path(val) == Path(path_str)


def test_safe_heuristic_rejects_json_like_strings():
    bad = '{"not": "a path"}'
    typ, val = SourceClassifier.classify_source(bad, Flags.NONE)
    # safe_is_path will return False => no read/bytes => fallback JSON_STR
    assert typ is SourceType.JSON_STR
    assert val == bad


def test_safe_flag_uses_only_safe_is_path(tmp_path):
    # With SAFE flag, skip FS_PROBE; safe_is_path says .json is path
    src = "config.json"
    typ, val = SourceClassifier.classify_source(src, Flags.SAFE)
    assert typ is SourceType.PATH
    assert val == Path(src)

    # SAFE rejects bad characters
    bad = "bad{name}.json"
    typ2, val2 = SourceClassifier.classify_source(bad, Flags.SAFE)
    assert typ2 is SourceType.JSON_STR
    assert val2 == bad


def test_unsafe_fs_probe_success(tmp_path, monkeypatch):
    # use a non-existent file under tmp_path
    target = tmp_path / "will_be_created.json"
    src = str(target)

    # Without FS_PROBE, unsafe => safe_is_path => .json => True => PATH
    typ1, _ = SourceClassifier.classify_source(src, Flags.NONE)
    assert typ1 is SourceType.PATH

    # With FS_PROBE, unsafe_is_path will touch & unlink => True => PATH
    typ2, val2 = SourceClassifier.classify_source(src, Flags.FS_PROBE)
    assert typ2 is SourceType.PATH
    # file should not actually remain
    assert not target.exists()


def test_unsafe_fs_probe_failure(tmp_path, monkeypatch):
    # simulate a path where touch will fail: monkeypatch Path.touch
    target = tmp_path / "cannot_touch.json"
    src = str(target)

    original_touch = Path.touch
    def fake_touch(self, *args, **kwargs):
        raise PermissionError("nope")

    monkeypatch.setattr(Path, "touch", fake_touch)

    # FS_PROBE => unsafe_is_path catches exception => returns False => fallback JSON_STR
    typ, val = SourceClassifier.classify_source(src, Flags.FS_PROBE)
    assert typ is SourceType.JSON_STR
    assert val == src

    # restore
    monkeypatch.setattr(Path, "touch", original_touch)


def test_fallback_non_stringifiable_object():
    class Weird:
        def __str__(self):
            raise RuntimeError("bad __str__")

    w = Weird()
    # classify_source will attempt str(source) in fallback and propagate the error
    with pytest.raises(RuntimeError):
        SourceClassifier.classify_source(w, Flags.NONE)

def test_fallback_non_stringifiable_object_with_safe():
    class Weird:
        def __str__(self):
            raise RuntimeError("bad __str__")

    w = Weird()
    # classify_source will attempt str(source) in fallback and propagate the error
    with pytest.raises(RuntimeError):
        SourceClassifier.classify_source(w, Flags.SAFE)

def test_fallback_non_stringifiable_object_with_fs_probe():
    class Weird:
        def __str__(self):
            raise RuntimeError("bad __str__")

    w = Weird()
    # classify_source will attempt str(source) in fallback and propagate the error
    with pytest.raises(RuntimeError):
        SourceClassifier.classify_source(w, Flags.FS_PROBE)

def test_fallback_non_stringifiable_object_with_is_json():
    class Weird:
        def __str__(self):
            raise RuntimeError("bad __str__")

    w = Weird()
    # classify_source will attempt str(source) in fallback and propagate the error
    with pytest.raises(RuntimeError):
        SourceClassifier.classify_source(w, Flags.IS_JSON)

if __name__ == "__main__":
    pytest.main([__file__])