import importlib
import logging
import sys
import pytest

from jsonio._utils import Backend, Flags
from jsonio.backend import load_backend

class DummyBackend:
    def __init__(self):
        self.initialized = True

@pytest.fixture(autouse=True)
def clear_import(monkeypatch):
    # Ensure fresh import state for each test
    monkeypatch.setattr(logging, 'info', lambda *args, **kwargs: None)
    monkeypatch.setattr(logging, 'error', lambda *args, **kwargs: None)
    yield

@ pytest.mark.parametrize("backend_enum, module_name, class_name", [
    (Backend.JSON, 'json_backend', 'JsonBackend'),
    (Backend.ORJSON, 'orjson_backend', 'OrjsonBackend'),
    (Backend.UJSON, 'ujson_backend', 'UjsonBackend'),
    (Backend.RAPIDJSON, 'rapidjson_backend', 'RapidjsonBackend'),
    (Backend.SIMPLEJSON, 'simplejson_backend', 'SimplejsonBackend'),
])
def test_load_backend_success(monkeypatch, backend_enum, module_name, class_name):
    # Mock import_module to provide a dummy module with the expected class
    dummy_module = type(sys)(module_name)
    setattr(dummy_module, class_name, DummyBackend)
    monkeypatch.setattr(importlib, 'import_module', lambda path: dummy_module)

    instance = load_backend(backend_enum, flags=[])
    assert isinstance(instance, DummyBackend), \
        f"Expected instance of {class_name} for backend {backend_enum}"


def test_load_backend_value_error():
    class FakeBackend:
        value = 'fake'

    with pytest.raises(ValueError) as exc:
        load_backend(FakeBackend, flags=[])
    assert 'Unsupported backend' in str(exc.value)


def test_load_backend_import_error_no_runtime_install(monkeypatch):
    # Simulate import_module raising ImportError
    monkeypatch.setattr(importlib, 'import_module', lambda path: (_ for _ in ()).throw(ImportError('missing')))

    with pytest.raises(ImportError) as exc:
        load_backend(Backend.JSON, flags=[])
    assert "not available. Please install" in str(exc.value)


def test_load_backend_runtime_install_success(monkeypatch):
    # simulate initial import failure
    calls = {'count': 0}
    def fake_import(path):
        calls['count'] += 1
        if calls['count'] == 1:
            raise ImportError('missing')
        # second call returns dummy
        module = type(sys)('json_backend')
        setattr(module, 'JsonBackend', DummyBackend)
        return module

    monkeypatch.setattr(importlib, 'import_module', fake_import)

    # Mock InstallerFactory
    class FakeInstaller:
        def install(self):
            return None

    class FakeInstallerFactory:
        @staticmethod
        def get_installer(backend):
            return FakeInstaller()

    monkeypatch.setitem(sys.modules, 'jsonio.backend._installer', type(sys)('_installer'))
    installer_module = sys.modules['jsonio.backend._installer']
    installer_module.InstallerFactory = FakeInstallerFactory

    result = load_backend(Backend.JSON, flags=[Flags.RUNTIME_INSTALL])
    assert isinstance(result, DummyBackend)


def test_load_backend_runtime_install_failure(monkeypatch):
    # simulate initial import failure
    def fake_import(path):
        raise ImportError('missing')

    monkeypatch.setattr(importlib, 'import_module', fake_import)

    # Mock InstallerFactory to raise on install
    class BadInstaller:
        def install(self):
            raise RuntimeError('install failed')

    class FakeInstallerFactory:
        @staticmethod
        def get_installer(backend):
            return BadInstaller()

    sys.modules['jsonio.backend._installer'] = type(sys)('_installer')
    sys.modules['jsonio.backend._installer'].InstallerFactory = FakeInstallerFactory

    with pytest.raises(ImportError) as exc:
        load_backend(Backend.JSON, flags=[Flags.RUNTIME_INSTALL])
    assert "Backend 'json' is not installed" in str(exc.value)

if __name__ == "__main__":
    pytest.main([__file__])