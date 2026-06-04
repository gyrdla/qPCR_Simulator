# core/config.py
import json, os
from typing import Dict, Any, Optional

CURRENT_VERSION = "2.0.0"

class AppConfig:
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.defaults = {
            "version": CURRENT_VERSION,
            "seed": None,
            "feature_flags": {
                "async_tasks": True,
                "blast_pipeline": False,
                "bio_variation": False,
                "iso_template": False
            },
            "ui": {"theme": "modern", "language": "tr"},
            "paths": {"sessions": "./sessions", "reports": "./reports"}
        }
        self.config = self._load_or_create()

    def _load_or_create(self) -> Dict[str, Any]:
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
            for k, v in self.defaults.items():
                if k not in loaded:
                    loaded[k] = v
            return loaded
        self._save(self.defaults)
        return self.defaults

    def _save(self, data: Dict[str, Any]):
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get(self, key: str, default=None):
        return self.config.get(key, default)

    def update(self, key: str, value: Any):
        self.config[key] = value
        self._save(self.config)

    def is_feature_enabled(self, feature: str) -> bool:
        return self.config.get("feature_flags", {}).get(feature, False)