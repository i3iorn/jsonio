# jsonio/config.py

from dataclasses import dataclass
from typing import Optional, Type
from jsonio._utils import Flags, DecoderClass
from jsonio.backend.protocol import JsonBackendProtocol


@dataclass(frozen=True)
class ReaderConfig:
    """
    Configuration for JSON reader.
    This class is used to store configuration options for the JSON reader.
    It is designed to be immutable (frozen=True) to ensure that the configuration
    remains consistent throughout the lifetime of the reader instance.

    Attributes:
        safe_mode (bool): If True, enables safe mode for backend resolution.
        runtime_install (bool): If True, allows runtime installation of backends.
        fs_probe (bool): If True, enables filesystem probing for source classification.
        force_is_json (bool): If True, forces the source to be treated as JSON.
        force_is_path (bool): If True, forces the source to be treated as a file path.
        backend_name (Optional[str]): The name of the backend to use.
        backend_class (Optional[Type[JsonBackendProtocol]]): The class of the backend to use.
        decoder_cls (DecoderClass): The decoder class to use for deserialization.

        resolver_flags (Flags): Flags that affect backend resolution.
        classification_flags (ReadFlags): Flags that affect source classification.

    """
    # ← Flags that affect *backend resolution* (SAFE, etc.)
    safe_mode: bool = False
    runtime_install: bool = False

    # ← Flags that affect *source classification* (FS_PROBE)
    fs_probe: bool = False

    # ← Explicit overrides at call‐time (IS_JSON / IS_PATH)
    force_is_json: bool = False
    force_is_path: bool = False

    # ← Backend choice
    backend_name: Optional[str] = None
    backend_class: Optional[Type[JsonBackendProtocol]] = None

    # ← Decoder choice for deserialization
    decoder_cls: DecoderClass = None

    @property
    def resolver_flags(self) -> Flags:
        f = Flags.NONE
        if self.safe_mode:
            f |= Flags.SAFE
        if self.runtime_install:
            f |= Flags.RUNTIME_INSTALL
        return f

    @property
    def classification_flags(self) -> Flags:
        rf = Flags.NONE
        if self.force_is_json:
            rf |= Flags.IS_JSON
        if self.force_is_path:
            rf |= Flags.IS_PATH
        if self.fs_probe:
            rf |= Flags.FS_PROBE
        return rf
