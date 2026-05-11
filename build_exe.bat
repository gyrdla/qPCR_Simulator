@echo off
echo [qPCR Simulator] .exe olusturuluyor...
call .venv\Scripts\activate.bat
pip install -q pyinstaller
pyinstaller --clean --onefile --windowed --name "qPCR_Simulator" --hidden-import=scipy.optimize --hidden-import=matplotlib.backends.backend_qt5agg main.py
echo.
echo [BASARILI] dist\qPCR_Simulator.exe hazir.
pause