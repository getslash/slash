from confetti import Config
from .utils.conf_utils import Doc, Cmdline

__all__ = ["config"]

config = Config({
    "runner": {
        "pdb": {
            "enabled" : True // Doc("Enter pdb on failures and errors") // Cmdline(on="--pdb"),
        }
    }
})
