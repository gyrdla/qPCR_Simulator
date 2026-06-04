# core/project_state.py
import json, os, datetime
from typing import Dict, Any, Optional
from core.config import AppConfig

class ProjectState:
    def __init__(self, config: AppConfig):
        self.config = config
        self.session_dir = config.get("paths", {}).get("sessions", "./sessions")
        self.report_dir = config.get("paths", {}).get("reports", "./reports")
        os.makedirs(self.session_dir, exist_ok=True)
        os.makedirs(self.report_dir, exist_ok=True)

    def create_session(self, session_id: Optional[str] = None) -> str:
        if not session_id:
            session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        return os.path.join(self.session_dir, f"session_{session_id}.json")

    def save(self, path: str, data: Dict[str, Any]):
        data["metadata"] = {
            "version": self.config.get("version"),
            "timestamp": datetime.datetime.now().isoformat(),
            "seed": self.config.get("seed")
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
        return path

    def load(self, path: str) -> Optional[Dict[str, Any]]:
        if not os.path.exists(path): return None
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)