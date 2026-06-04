# analysis/lims_export.py
import csv, json, os, datetime
from typing import Dict, List

class LIMSExporter:
    def __init__(self, output_dir: str = "./exports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def export_csv(self, session_id: str, data: Dict):
        path = os.path.join(self.output_dir, f"{session_id}_lims.csv")
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=data['parameters'].keys() | data['results'].keys())
            writer.writeheader()
            writer.writerow({**data['parameters'], **data['results']})
        return path

    def export_json(self, session_id: str, data: Dict):
        path = os.path.join(self.output_dir, f"{session_id}_lims.json")
        data['export_metadata'] = {'timestamp': datetime.datetime.now().isoformat(), 'format': 'LIMS_v1.0'}
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
        return path

    def batch_export(self, sessions: List[Dict]):
        for s in sessions:
            sid = s.get('id', 'unknown')
            self.export_csv(sid, s)
            self.export_json(sid, s)
        return f"{len(sessions)} session exported to {self.output_dir}"