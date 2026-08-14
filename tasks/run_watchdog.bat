@echo off
:: Ejecutar como tarea separada del pipeline, días hábiles 20:35 hs.
cd /d "C:\Users\Mlaxague\Projects\IEP"
if not exist logs mkdir logs
py src\pipeline\watchdog.py --deadline 20:30 >> logs\watchdog.log 2>&1
exit /b %errorlevel%
