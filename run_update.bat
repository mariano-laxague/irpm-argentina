@echo off
:: ============================================================
:: run_update.bat — Actualizacion diaria del IEP Argentina
:: Configurar en Task Scheduler: lunes a viernes, 18:30 hs
:: ============================================================

cd /d "C:\Users\Mlaxague\Projects\IEP"

:: Crear directorio de logs si no existe
if not exist logs mkdir logs

:: Nombre del log con fecha (YYYYMMDD)
for /f %%d in ('powershell -command "Get-Date -Format yyyyMMdd"') do set TODAY=%%d
set LOGFILE=logs\update_%TODAY%.log

:: Separador en el log
echo. >> "%LOGFILE%"
echo ============================================================ >> "%LOGFILE%"
powershell -command "Get-Date -Format 'yyyy-MM-dd HH:mm:ss'" >> "%LOGFILE%"
echo ============================================================ >> "%LOGFILE%"

:: Ejecutar pipeline y redirigir output al log
py src\pipeline\update_daily.py >> "%LOGFILE%" 2>&1

:: Verificar resultado
if %errorlevel% neq 0 (
    echo ERROR: pipeline fallo con codigo %errorlevel% >> "%LOGFILE%"
    exit /b %errorlevel%
)

exit /b 0
