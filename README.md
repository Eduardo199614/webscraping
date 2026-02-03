@echo off
cd /d "C:\Users\Lenovo LOQ\Documents\GitHub\webscraping"

echo ================================
echo Ejecutando scraper: PATIOTUERCA
echo ================================
python -m paginas.Autocor.main --source patiotuerca

echo.
echo ================================
echo Ejecutando scraper: AUTOCOR
echo ================================
python -m paginas.Autocor.main

echo.
echo ===== TODOS LOS PROCESOS HAN TERMINADO =====
pause
