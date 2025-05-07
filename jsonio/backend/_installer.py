import subprocess
from jsonio._utils import Backend


class _Installer:
    """
    Base class for backend installers.
    """
    def __init__(self, backend: Backend) -> None:
        if not isinstance(backend, Backend):
            raise TypeError(f"Expected Backend enum, got {type(backend)}")
        self.backend = backend

    def install(self) -> None:
        raise NotImplementedError("Install method not implemented")

    def uninstall(self) -> None:
        raise NotImplementedError("Uninstall method not implemented")


class _PipInstaller(_Installer):
    """
    Generic pip-based installer.
    """
    def __init__(self, backend: Backend, package_name: str) -> None:
        super().__init__(backend)
        self.package_name = package_name

    def install(self) -> None:
        subprocess.check_call(["pip", "install", self.package_name])

    def uninstall(self) -> None:
        subprocess.check_call(["pip", "uninstall", "-y", self.package_name])


class InstallerFactory:
    """
    Factory for backend installers.
    """
    _INSTALLERS = {
        Backend.ORJSON: lambda: _PipInstaller(Backend.ORJSON, "orjson"),
        Backend.UJSON: lambda: _PipInstaller(Backend.UJSON, "ujson"),
        Backend.RAPIDJSON: lambda: _PipInstaller(Backend.RAPIDJSON, "python-rapidjson"),
        Backend.SIMPLEJSON: lambda: _PipInstaller(Backend.SIMPLEJSON, "simplejson"),
        # json and ijson assumed to be standard or core dependencies
    }

    @staticmethod
    def get_installer(backend: Backend) -> _Installer:
        if backend in InstallerFactory._INSTALLERS:
            return InstallerFactory._INSTALLERS[backend]()
        raise ValueError(f"No installer registered for backend: {backend}")
