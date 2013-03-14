from confetti import Config
from .utils.conf_utils import Doc, Cmdline

__all__ = ["config"]

config = Config({
    "debug" : {
        "enabled" : False // Doc("Enter pdb on failures and errors") // Cmdline(on="--pdb"),
    }
})
