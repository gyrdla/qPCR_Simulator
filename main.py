# main.py
import sys, os
from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow
from gui.error_logger import ErrorLogger

def exception_hook(exc_type, exc_value, exc_traceback):
    """Global exception handler → ErrorLogger'a yönlendir"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger = ErrorLogger()
    logger.log(exc_value, "Global Exception")

def main():
    sys.excepthook = exception_hook
    
    app = QApplication(sys.argv)
    app.setApplicationName("qPCR Simulator v2.1")
    app.setOrganizationName("Digital Twin Lab")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()