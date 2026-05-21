from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, List
import yaml
from dacite import from_dict


@dataclass
class DiscordConfig:
    token: str = ""
    developer_ids: List[int] = field(default_factory=list)


@dataclass
class DatabaseConfig:
    filename: str = ""


@dataclass
class GoogleConfig:
    google_client_id: str = ""
    google_client_secret: str = ""
    google_refresh_token: str = ""


@dataclass
class Config:
    discord: DiscordConfig = field(default_factory=DiscordConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    google: GoogleConfig = field(default_factory=GoogleConfig)


def _load_yaml_config(path: str) -> dict[str, Any]:
    with open(path, "r") as file:
        raw_cfg = yaml.safe_load(file) or {}
    return raw_cfg


def load_config() -> Config:
    cfg_path = Path(__file__).resolve().parent.parent / "config" / "config.yaml"
    raw_cfg = _load_yaml_config(str(cfg_path))

    return from_dict(data_class=Config, data=raw_cfg)


def _save_yaml_config(path: str, data: dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as file:
        yaml.safe_dump(data, file, sort_keys=False, allow_unicode=True)


def save_config(cfg: Config) -> None:
    path = Path(__file__).resolve().parent.parent / "config" / "config.yaml"

    data = asdict(cfg)

    out = {
        "discord": data.get("discord", {}),
        "database": data.get("database", {}),
        "google": data.get("google", {}),
    }

    _save_yaml_config(str(path), out)

    global CONFIG
    CONFIG = cfg


CONFIG = load_config()
