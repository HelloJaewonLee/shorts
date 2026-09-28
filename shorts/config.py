import copy
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PATH = ROOT / "config" / "default.yaml"


def merge(base: dict, over: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = merge(out[k], v)
        else:
            out[k] = v
    return out


def load(path: Path | None = None) -> dict:
    cfg = yaml.safe_load(DEFAULT_PATH.read_text(encoding="utf-8"))
    if path and path.exists():
        cfg = merge(cfg, yaml.safe_load(path.read_text(encoding="utf-8")) or {})
    return cfg


def save(cfg: dict, path: Path) -> None:
    path.write_text(yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False), encoding="utf-8")


def set_path(cfg: dict, dotted: str, value) -> None:
    """'caption.size' 같은 점 경로에 값을 넣는다. 없는 키면 KeyError."""
    keys = dotted.split(".")
    node = cfg
    for k in keys[:-1]:
        node = node[k]
    if keys[-1] not in node:
        raise KeyError(dotted)
    node[keys[-1]] = value
