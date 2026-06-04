# gui/error_logger.py
import os, datetime, traceback, sys
from PyQt6.QtCore import QObject, pyqtSignal

class ErrorLogger(QObject):
    error_logged = pyqtSignal(str)
    
    def __init__(self, log_dir: str = "./logs"):
        super().__init__()
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        self.log_file = os.path.join(log_dir, f"error_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    
    def log(self, error: Exception, context: str = ""):
        """Hatayı dosyaya yazar ve sinyal olarak UI'ya iletir"""
        timestamp = datetime.datetime.now().isoformat()
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"⏰ Zaman: {timestamp}\n")
            f.write(f"📍 Bağlam: {context}\n")
            f.write(f"❌ Hata: {type(error).__name__}: {error}\n")
            f.write(f"🔍 Traceback:\n{traceback.format_exc()}\n")
            f.write(f"🖥️ Python: {sys.version}\n")
            f.write(f"🪟 Platform: {sys.platform}\n")
        self.error_logged.emit(f"❌ Hata loglandı: {self.log_file}\n{type(error).__name__}: {error}")
    
    def get_latest_log(self) -> str:
        """En son log dosyasının yolunu döner"""
        logs = [f for f in os.listdir(self.log_dir) if f.startswith("error_")]
        if not logs: return "Log dosyası bulunamadı."
        latest = sorted(logs)[-1]
        return os.path.join(self.log_dir, latest)