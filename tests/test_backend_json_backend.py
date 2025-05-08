# tests/test_json_backend_extended.py

import io
import json
import pytest

from json.decoder import JSONDecodeError
from jsonio.backend.json_backend import JsonBackend
from jsonio._utils import DecoderClass

@pytest.fixture
def backend():
    return JsonBackend()

class AlwaysFailDecoder(json.JSONDecoder):
    """A decoder that always raises."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    def decode(self, s):
        raise RuntimeError("decoder failure")

class CustomDecoder(json.JSONDecoder):
    """A custom decoder that returns a specific value."""
    def decode(self, s):
        return {"decoded": True}

@pytest.mark.parametrize("obj", [
    123,
    "hello",
    {"a": [1, 2, 3], "b": {"nested": True}},
    [1, 2, 3],
])
def test_dumps_produces_standard_json(backend, obj):
    """dumps() should match json.dumps()."""
    assert backend.dumps(obj) == json.dumps(obj)


def test_dump_writes_to_file_like(backend):
    """dump() should write the same JSON string to the given file pointer."""
    obj = {"foo": "bar", "num": 42}
    buffer = io.StringIO()
    backend.dump(obj, buffer)
    buffer.seek(0)
    assert buffer.read() == json.dumps(obj)


@pytest.mark.parametrize("s,data", [
    ('{"x":1}', {"x": 1}),
    ('[true, false, null]', [True, False, None]),
])
def test_loads_with_default_backend(backend, s, data):
    """loads() should parse JSON strings correctly with the stdlib loader."""
    assert backend.loads(s) == data


def test_load_uses__load_and_returns_none(backend, monkeypatch):
    s = '{"test": 99}'
    buffer = io.StringIO(s)
    called = {}

    def fake_load(fp, **kw):
        called['args'] = (fp.read(), kw)
        return {"ignored": True}

    monkeypatch.setattr(backend, "_load", lambda fp, func, **kw: fake_load(fp, **kw))

    result = backend.load(buffer)
    assert result == {"ignored": True}
    # ensure fake_load actually ran on the buffer contents
    assert called['args'][0] == s


def test__load_with_custom_function(backend):
    """_load should forward fp and kwargs to any provided function."""
    sentinel = object()

    def dummy(fp, **parameters):
        return ("ok", fp, parameters)

    ret = backend._load("INPUT", dummy, foo=1, bar=2)
    assert ret == ("ok", "INPUT", {"foo": 1, "bar": 2})


def test_loads_with_custom_decoder_class(backend):
    """loads() should pass decoder_class as 'cls' to json.loads."""
    s = '{"irrelevant": "data"}'
    result = backend.loads(s, decoder_class=CustomDecoder)
    assert result == {"decoded": True}

@pytest.mark.parametrize("raw", [
    b'{"x": 1}',                          # bytes payload
    bytearray(b'{"x": 1}'),               # bytearray payload
])
def test_loads_accepts_bytes_and_bytearray(backend, raw):
    assert backend.loads(raw) == {"x": 1}

def test_loads_rejects_invalid_type():
    # Passing an int should immediately TypeError
    with pytest.raises(TypeError):
        JsonBackend().loads(12345)        # not str, bytes or bytearray

def test_loads_bom_prefix_raises_decode_error():
    # Leading UTF-8 BOM in string should error
    s = "\ufeff{\"foo\": \"bar\"}"
    with pytest.raises(JSONDecodeError) as ei:
        JsonBackend().loads(s)
    assert "Unexpected UTF-8 BOM" in str(ei.value)

def test_loads_invalid_json_raises_JSONDecodeError(backend):
    with pytest.raises(JSONDecodeError):
        backend.loads('{"incomplete": true')  # missing closing }

def test_loads_with_always_fail_decoder(backend):
    # Make sure custom decoder exceptions bubble up
    with pytest.raises(RuntimeError):
        backend.loads('{"whatever": 0}', decoder_class=AlwaysFailDecoder)

def test_dumps_non_serializable_raises_type_error(backend):
    with pytest.raises(TypeError):
        backend.dumps({1, 2, 3})            # sets aren’t JSON serializable

def test_dump_writes_binary_fp_and_text_fp(backend):
    obj = {"binary": True}
    # text-mode
    text_buf = io.StringIO()
    backend.dump(obj, text_buf)
    assert text_buf.getvalue() == json.dumps(obj)

    # binary-mode (BytesIO): json.dump calls .write() with str, so this will error
    bin_buf = io.BytesIO()
    with pytest.raises(TypeError):
        backend.dump(obj, bin_buf)

def test_load_from_binary_filepointer(backend):
    # io.BytesIO should be readable and parse
    bin_fp = io.BytesIO(b'{"nested": [1,2,3]}')
    assert backend.load(bin_fp) == {"nested": [1,2,3]}

def test_load_from_string_filepointer(backend):
    # io.StringIO
    s = '{"x": 42}'
    fp = io.StringIO(s)
    assert backend.load(fp) == {"x": 42}

def test_load_with_wrong_fp_type_raises_attribute_error(backend):
    # passing a plain string to load should complain about missing .read()
    with pytest.raises(AttributeError):
        backend.load('{"not": "fp"}')

def test__load_forwards_all_non_none_kwargs(monkeypatch, backend):
    called = {}
    def dummy(fp, **params):
        return fp, params

    # even if encoding is provided, our code filters out None but keeps explicit strings
    result = backend._load("PAYLOAD", dummy, foo=1, bar=None, encoding="utf-8")
    assert result == ("PAYLOAD", {"foo": 1, "encoding": "utf-8"})

def test_loads_with_encoding_arg_ignored(monkeypatch, backend):
    # if encoding is passed but None, it should simply go away
    # patch json.loads to capture what parameters it sees
    seen = {}
    def fake_load(fp, **params):
        seen['params'] = params
        return {"ok": True}
    monkeypatch.setattr(json, "loads", fake_load)

    out = backend.loads('{"a":1}', encoding=None)
    assert out == {"ok": True}
    assert 'encoding' not in seen['params']

def test_loads_with_decoder_class_and_encoding(monkeypatch, backend):
    # ensure both decoder_class and encoding pass through correctly when non-None
    seen = {}
    class MyDecoder(json.JSONDecoder):
        pass

    def fake_load(fp, **params):
        seen.update(params)
        return {"decoded": True}

    monkeypatch.setattr(json, "loads", fake_load)
    out = backend.loads('{"a":1}', encoding="utf-8", decoder_class=MyDecoder)
    assert out == {"decoded": True}
    assert seen["cls"] is MyDecoder
    assert seen["encoding"] == "utf-8"


def test_loads_with_decoder_class_only(monkeypatch, backend):
    # ensure decoder_class passes through correctly when non-None
    seen = {}
    class MyDecoder(json.JSONDecoder):
        pass

    def fake_load(fp, **params):
        seen.update(params)
        return {"decoded": True}

    monkeypatch.setattr(json, "loads", fake_load)
    out = backend.loads('{"a":1}', decoder_class=MyDecoder)
    assert out == {"decoded": True}
    assert seen["cls"] is MyDecoder
    assert "encoding" not in seen

def test_loads_with_encoding_only(monkeypatch, backend):
    # ensure encoding passes through correctly when non-None
    seen = {}
    def fake_load(fp, **params):
        seen.update(params)
        return {"decoded": True}

    monkeypatch.setattr(json, "loads", fake_load)
    out = backend.loads('{"a":1}', encoding="utf-8")
    assert out == {"decoded": True}
    assert seen["encoding"] == "utf-8"
    assert "cls" not in seen

# ─── dumps() WITH ENCODING PARAMETER ────────────────────────────────────────────

def test_dumps_ignores_encoding_keyword(backend):
    obj = {"a": 1, "b": 2}
    # dumps should ignore the encoding kwarg and behave like json.dumps
    assert backend.dumps(obj, encoding="utf-8") == json.dumps(obj)

# ─── ROUND-TRIP Unicode & Whitespace ──────────────────────────────────────────

def test_dumps_and_loads_with_unicode(backend):
    obj = {"emoji": "😀", "chinese": "汉字", "arabic": "مرحبا"}
    dumped = backend.dumps(obj)
    # JSON always uses escape sequences for non-ASCII by default
    assert "\\u" in dumped
    loaded = backend.loads(dumped)
    assert loaded == obj

def test_loads_with_extra_whitespace(backend):
    s = "  \n\t {  \"x\" :  [ 1 , 2 ,   3 ] }  \r\n"
    assert backend.loads(s) == {"x": [1, 2, 3]}

# ─── INVALID JSON IN load() ───────────────────────────────────────────────────

def test_load_invalid_json_in_filepointer(backend):
    fp = io.StringIO('{"incomplete":')
    with pytest.raises(JSONDecodeError):
        backend.load(fp)

# ─── dump() TO VARIOUS FP MODES ───────────────────────────────────────────────

def test_dump_with_encoding_arg_to_text_fp(backend):
    # passing encoding to dump should not interfere on text file
    obj = {"foo": "bar"}
    buf = io.StringIO()
    backend.dump(obj, buf, encoding="utf-8")
    assert buf.getvalue() == json.dumps(obj)

def test_dump_non_writable_fp_raises(backend):
    class NoWrite:
        def read(self): pass  # but no write()
    with pytest.raises(AttributeError):
        backend.dump({"x": 1}, NoWrite())

# ─── VERY LARGE OR NESTED DATA ────────────────────────────────────────────────

def test_dumps_and_loads_large_nested_structure(backend):
    # generate a deep nested dict
    obj = current = {}
    for i in range(1000):
        current["level"] = i
        current["next"] = {}
        current = current["next"]
    dumped = backend.dumps(obj)
    loaded = backend.loads(dumped)
    assert isinstance(loaded, dict)
    # check a few deep values
    v = loaded
    for expected in [0, 1, 2, 3]:
        assert v["level"] == expected
        v = v["next"]

# ─── round-trip via load/dump chain ───────────────────────────────────────────

def test_dump_then_load_returns_equivalent(backend, tmp_path):
    obj = {"list": [1, 2, {"a": True}], "num": 3.14}
    path = tmp_path / "data.json"
    with open(path, "w", encoding="utf-8") as fp:
        backend.dump(obj, fp)
    with open(path, "r", encoding="utf-8") as fp:
        loaded = backend.load(fp)
    assert loaded == obj

# ─── ensure no unexpected parameters slip through ────────────────────────────

def test_internal__load_signature_filtering(monkeypatch, backend):
    seen = {}
    def fake(fp, **params):
        seen.update(params)
        return {}
    # simulate passing an unsupported kw
    monkeypatch.setattr(backend, "loads", fake)
    backend.loads('{"a":1}', encoding=None, decoder_class=None, foo="bar")
    assert seen == {"foo": "bar", "encoding": None, "decoder_class": None}

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
