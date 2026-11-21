"""Load pure protocol code without importing Home Assistant."""
import importlib.util
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "custom_components/hcalory_ble_modern"
package = types.ModuleType("probe_package")
package.__path__ = [str(PACKAGE)]
sys.modules.setdefault("probe_package", package)


def load(name):
    fullname = f"probe_package.{name}"
    if fullname in sys.modules:
        return sys.modules[fullname]
    spec = importlib.util.spec_from_file_location(fullname, PACKAGE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[fullname] = module
    spec.loader.exec_module(module)
    return module


protocol = load("protocol")
