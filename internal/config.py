from dataclasses import dataclass
from typing import Any, Dict

import utils

@dataclass
class DatabaseConfig:
    filename: str = "sqlite.db"

@dataclass
class Config:
    database: DatabaseConfig

def _load_yaml_cfg(path: str) -> Dict[str, Any]:
    try:
        import yaml

        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        # Fallback simple parser for tiny YAML subset used in this project
        data: Dict[str, Any] = {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                current = data
                for raw in f.readlines():
                    line = raw.strip()
                    if not line or line.startswith("#"):
                        continue
                    if ":" in line:
                        key, val = line.split(":", 1)
                        key = key.strip()
                        val = val.strip()
                        if val == "":
                            # start of mapping
                            current[key] = {}
                            parent = current
                            current = current[key]
                        else:
                            # scalar value
                            # remove surrounding quotes if present
                            if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                                val = val[1:-1]
                            current[key] = val
            return data
        except Exception:
            return {}


def load_config() -> Config:
    cfg_path = utils.ROOT_DIR / "config" / "config.yaml"
    data = _load_yaml_cfg(str(cfg_path)) if cfg_path.exists() else {}
    db_section = data.get("database", {}) or {}
    filename = db_section.get("filename") or "sqlite.db"
    return Config(database=DatabaseConfig(filename=filename))


CONFIG = load_config()
