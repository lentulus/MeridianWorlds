import tomllib
from pathlib import Path

_ROOT = Path(__file__).parent
with open(_ROOT / "meridian/config.toml", "rb") as _f:
    _meridian = tomllib.load(_f)

STARFIELD_DB = "/Users/lentulus/databases/starfield.db"
WORLDS_DB = "/Users/lentulus/databases/world.db"

MERIDIAN_DATA_PATHS = [
    Path(_meridian["immutable"]["path"]),
    _ROOT / _meridian["volatile"]["path"],
]

_volatile = _ROOT / _meridian["volatile"]["path"]
_dbs = _meridian["volatile"]["databases"]
COLONY_DB = _volatile / _dbs["colonybase"]
SHIP_DB   = _volatile / _dbs["shipbase"]
